import itertools
import os
import zipfile
import hashlib
from io import BytesIO
from tempfile import TemporaryFile

from flask import current_app, send_file
from flask_restful import Resource, reqparse
from flask_restful.inputs import boolean
from werkzeug.datastructures import FileStorage
from sqlalchemy.orm import selectinload

from zesje.api._helpers import _shuffle
from zesje.api.problems import problem_to_data
from ..pdf_generation import generate_pdfs, join_pdfs
from ..pdf_generation import page_is_size, save_with_even_pages
from ..pdf_generation import write_finalized_exam
from ..database import db, Exam, ExamWidget, Submission, FeedbackOption, token_length
from .submissions import sub_to_data
from ..pregrader import BLANK_FEEDBACK_NAME


def _get_exam_dir(exam_id):
    return os.path.join(
        current_app.config['DATA_DIRECTORY'],
        f'{exam_id}_data',
    )


def checkboxes(exam):
    """
    Returns all multiple choice question check boxes for one specific exam

    Parameters
    ----------
        exam: the exam

    Returns
    -------
        A list of tuples with checkbox data.
        Each tuple is represented as (x, y, page, label)

        Where
        x: x position
        y: y position
        page: page number
        label: checkbox label
    """
    cb_data = []
    for problem in exam.problems:
        page = problem.widget.page
        cb_data += [(cb.x, cb.y, page, cb.label) for cb in problem.mc_options]

    return cb_data


def add_blank_feedback(problems):
    """
    Add the blank feedback option to each problem.
    """
    for p in problems:
        db.session.add(FeedbackOption(problem_id=p.id, text=BLANK_FEEDBACK_NAME, score=0))

    db.session.commit()


def generate_exam_token(exam_id, exam_name, exam_pdf):
    hasher = hashlib.sha1()
    hasher.update(exam_pdf)
    hasher.update(f'{exam_id},{exam_name}'.encode('utf-8'))
    return hasher.hexdigest()[0:12]


class Exams(Resource):

    get_parser = reqparse.RequestParser()
    get_parser.add_argument('only_metadata', type=boolean, required=False)
    get_parser.add_argument('shuffle_seed', type=int, required=False)

    def get(self, exam_id=None):
        args = self.get_parser.parse_args()
        if exam_id:
            if args.only_metadata:
                return self._get_single_metadata(exam_id, args.shuffle_seed)
            return self._get_single(exam_id)
        else:
            return self._get_all()

    def delete(self, exam_id):
        exam = Exam.query.get(exam_id)
        if exam is None:
            return dict(status=404, message='Exam does not exist.'), 404
        elif exam.finalized:
            return dict(status=409, message='Cannot delete a finalized exam.'), 409
        elif Submission.query.filter(Submission.exam_id == exam.id).count():
            return dict(status=500, message='Exam is not finalized but already has submissions.'), 500
        else:
            # All corresponding solutions, scans and problems are automatically deleted
            db.session.delete(exam)
            db.session.commit()

            return dict(status=200, message="ok"), 200

    def _get_all(self):
        """get list of uploaded exams.

        Returns
        -------
        list of:
            id : int
                exam name
            name : str
                exam ID
            submissions : int
                Number of submissions
        """
        return [
            {
                'id': ex.id,
                'name': ex.name,
                'submissions': len(ex.submissions)
            }
            for ex in Exam.query.order_by(Exam.id).all()
        ]

    def _get_single(self, exam_id):
        """Get detailed information about a single exam

        URL Parameters
        --------------
        exam_id : int
            exam ID

        Returns
        -------
        id : int
            exam ID
        name : str
            exam name
        submissions
            list of submissions for this exam
        problems
            list of problems defined for this exam
        widgets
            list of widgets in this exam
        """
        # Load exam using the following most efficient strategy
        exam = Exam.query.options(selectinload(Exam.submissions).
                                  subqueryload(Submission.solutions)).get(exam_id)

        if exam is None:
            return dict(status=404, message='Exam does not exist.'), 404

        submissions = [sub_to_data(sub) for sub in exam.submissions]

        # Sort submissions by selecting those with students assigned, then by
        # student number, then by copy number.
        # TODO: This is a minimal fix of #166, to be replaced later.
        submissions = sorted(
            submissions,
            key=(lambda s: (bool(s['student']) and -s['student']['id'], s['id']))
        )

        return {
            'id': exam_id,
            'name': exam.name,
            'submissions': submissions,
            'problems': [problem_to_data(prob) for prob in exam.problems],  # Sorted by prob.id
            'widgets': [
                {
                    'id': widget.id,
                    'name': widget.name,
                    'x': widget.x,
                    'y': widget.y,
                    'type': widget.type
                } for widget in exam.widgets  # Sorted by widget.id
            ],
            'finalized': exam.finalized,
            'gradeAnonymous': exam.grade_anonymous,
        }

    def _get_single_metadata(self, exam_id, shuffle_seed):
        """ Serves metadata for an exam.
        Shuffles submissions based on the grader ID.

        Parameters
        ----------
        exam_id : int
            id of exam to get metadata for.
        shuffle_seed : int
            id of the grader.

        Returns
        -------
        the exam metadata.

        """

        exam = Exam.query.get(exam_id)
        if exam is None:
            return dict(status=404, message='Exam does not exist.'), 404

        return {
            'exam_id': exam.id,
            'submissions': [
                {
                    'id': sub.copy_number,
                    'student': {
                        'id': sub.student.id,
                        'firstName': sub.student.first_name,
                        'lastName': sub.student.last_name,
                        'email': sub.student.email
                    } if sub.student else None
                } for sub in _shuffle(exam.submissions, shuffle_seed, key_extractor=lambda s: s.id)
            ],
            'problems': [
                {
                    'id': problem.id,
                    'name': problem.name,
                } for problem in exam.problems]

        }

    post_parser = reqparse.RequestParser()
    post_parser.add_argument('pdf', type=FileStorage, required=True, location='files')
    post_parser.add_argument('exam_name', type=str, required=True, location='form')

    def post(self):
        """Add a new exam.

        Parameters
        ----------
        pdf : file
            raw pdf file.
        exam_name: str
            name for the exam

        Returns
        -------
        id : int
            exam ID
        """

        args = self.post_parser.parse_args()
        exam_name = args['exam_name']
        pdf_data = args['pdf']

        format = current_app.config['PAGE_FORMAT']

        if not page_is_size(pdf_data, current_app.config['PAGE_FORMATS'][format], tolerance=0.01):
            return (
                dict(status=400,
                     message=f'PDF page size is not {format}.'),
                400
            )

        exam = Exam(
            name=exam_name,
        )

        exam.widgets = [
            ExamWidget(
                name='student_id_widget',
                x=50,
                y=50,
                exam=exam,
            ),
            ExamWidget(
                name='barcode_widget',
                x=500,
                y=40,
                exam=exam,
            ),
        ]

        db.session.add(exam)
        db.session.commit()  # so exam gets an id
        exam.token = generate_exam_token(exam.id, exam_name, pdf_data.read())
        pdf_data.seek(0)
        db.session.commit()

        exam_dir = _get_exam_dir(exam.id)
        pdf_path = os.path.join(exam_dir, 'exam.pdf')
        os.makedirs(exam_dir, exist_ok=True)

        save_with_even_pages(pdf_path, args['pdf'])

        print(f"Added exam {exam.id} (name: {exam_name}, token: {exam.token}) to database")

        return {
            'id': exam.id
        }

    put_parser = reqparse.RequestParser()
    put_parser.add_argument('finalized', type=bool, required=False)
    put_parser.add_argument('grade_anonymous', type=bool, required=False)

    def put(self, exam_id):
        exam = Exam.query.get(exam_id)
        if exam is None:
            return dict(status=404, message='Exam does not exist.'), 404

        args = self.put_parser.parse_args()

        if args['finalized'] is None:
            pass
        elif args['finalized']:
            add_blank_feedback(exam.problems)

            exam_dir, student_id_widget, _, exam_path, cb_data = _exam_generate_data(exam)
            write_finalized_exam(exam_dir, exam_path, student_id_widget.x, student_id_widget.y, cb_data)

            exam.finalized = True
            db.session.commit()
            return dict(status=200, message="ok"), 200
        else:
            return dict(status=403, message=f'Exam can not be unfinalized'), 403

        if args['grade_anonymous'] is not None:
            exam.grade_anonymous = args['grade_anonymous']
            db.session.commit()
            return dict(status=200, message="ok"), 200

        return dict(status=400, message=f'One of finalized or anonymous must be present'), 400

    patch_parser = reqparse.RequestParser()
    patch_parser.add_argument('name', type=str, required=True)

    def patch(self, exam_id):
        """Update the name of an existing exam.

        Parameters
        ----------
        name: str
            name for the exam
        """

        exam = Exam.query.get(exam_id)
        if exam is None:
            return dict(status=404, message='Exam does not exist.'), 404

        args = self.patch_parser.parse_args()
        name = args['name'].strip()
        if not name:
            return dict(status=400, message='Exam name is empty.'), 400

        exam.name = name
        db.session.commit()

        return dict(status=200, message='ok'), 200


class ExamSource(Resource):

    def get(self, exam_id):

        exam = Exam.query.get(exam_id)

        if exam is None:
            return dict(status=404, message='Exam does not exist.'), 404

        exam_dir = _get_exam_dir(exam.id)

        return send_file(
            os.path.join(exam_dir, 'exam.pdf'),
            cache_timeout=0,
            mimetype='application/pdf')


class ExamGeneratedPdfs(Resource):

    def _get_generated_exam_dir(self, exam_dir):
        return os.path.join(
            exam_dir,
            'generated_pdfs'
        )

    def _get_paths_for_range(self, generated_pdfs_dir, copies_start, copies_end):
        copy_nums = range(copies_start, copies_end + 1)
        pdf_paths = [
            os.path.join(
                generated_pdfs_dir,
                current_app.config['OUTPUT_PDF_FILENAME_FORMAT'].format(copy_num))
            for copy_num
            in copy_nums
        ]
        return pdf_paths, copy_nums

    def _generate_exam_pdfs(self, exam, pdf_paths, copy_nums):
        """
        Generate and save separate exam PDFs for each copy to
        prepare for the user downloading them.

        This function retrieves the data necessary to generate
        the PDFs and calls the appropriate generation function.

        Parameters
        ----------
        exam : Exam
            The exam to generate the PDFs for
        pdf_paths : list of paths
            The location to save each PDF
        copy_nums: list of ints
            The copy numbers to generate
        """
        exam_dir, _, barcode_widget, exam_path, _ = _exam_generate_data(exam)

        generate_pdfs(
            exam_pdf_file=exam_path,
            copy_nums=copy_nums,
            output_paths=pdf_paths,
            exam_token=exam.token,
            datamatrix_x=barcode_widget.x,
            datamatrix_y=barcode_widget.y
        )

    get_parser = reqparse.RequestParser()
    get_parser.add_argument('copies_start', type=int, required=True)
    get_parser.add_argument('copies_end', type=int, required=True)
    get_parser.add_argument('type', type=str, required=True)

    def get(self, exam_id):
        """Generates the exams with datamatrices and copy numbers.

        A range is given. Ranges should be starting from 1.

        Parameters
        ----------
        copies_start : int
            start of the range of exam pdfs you want to get
        copies_end : int
            end of the range of exam pdfs you want to get
        type: str
            One of "zip", "pdf"
            the pdf option will give a large pdf consisting of concatenated
            exams. Zip will get a zip with all exams as separate files.

        Returns
        -------
        the file : File
            The requested file (zip or pdf)
        """

        args = self.get_parser.parse_args()

        copies_start = args.get('copies_start')
        copies_end = args.get('copies_end')

        exam = Exam.query.get(exam_id)
        if exam is None:
            return dict(status=404, message='Exam does not exist.'), 404
        if not exam.finalized:
            msg = f'Exam is not finalized.'
            return dict(status=403, message=msg), 403

        if copies_end < copies_start:
            msg = f'copies_end should be larger than copies_start'
            return dict(status=400, message=msg), 400
        if copies_start <= 0:
            msg = f'copies_start should be larger than 0'
            return dict(status=400, message=msg), 400

        exam_dir = _get_exam_dir(exam_id)
        generated_pdfs_dir = self._get_generated_exam_dir(exam_dir)

        os.makedirs(generated_pdfs_dir, exist_ok=True)

        pdf_paths, copy_nums = self._get_paths_for_range(generated_pdfs_dir, copies_start, copies_end)

        generate_selectors = [not os.path.exists(pdf_path) for pdf_path in pdf_paths]

        if any(generate_selectors):
            pdf_paths_to_generate = itertools.compress(pdf_paths, generate_selectors)
            copy_nums_to_generate = itertools.compress(copy_nums, generate_selectors)
            self._generate_exam_pdfs(exam, pdf_paths_to_generate, copy_nums_to_generate)

        output_file = TemporaryFile()

        if args['type'] == 'pdf':
            join_pdfs(
                output_file,
                pdf_paths,
            )
            attachment_filename = f'{exam.name}_{copies_start}-{copies_end}.pdf'
            mimetype = 'application/pdf'
        elif args['type'] == 'zip':
            with zipfile.ZipFile(output_file, 'w') as zf:
                for pdf_path in pdf_paths:
                    zf.write(
                        pdf_path,
                        os.path.basename(pdf_path)
                    )
            attachment_filename = f'{exam.name}_{copies_start}-{copies_end}.zip'
            mimetype = 'application/zip'
        else:
            msg = f'type must be one of ["pdf", "zip"]'
            return dict(status=400, message=msg), 400

        output_file.seek(0)

        return send_file(
            output_file,
            cache_timeout=0,
            attachment_filename=attachment_filename,
            as_attachment=True,
            mimetype=mimetype)


class ExamPreview(Resource):

    def get(self, exam_id):
        exam = Exam.query.get(exam_id)
        if exam is None:
            return dict(status=404, message='Exam does not exist.'), 404

        intermediate_file = BytesIO()

        exam_dir, student_id_widget, barcode_widget, exam_path, cb_data = _exam_generate_data(exam)

        # Generate generic overlay
        generate_pdfs(
            exam_pdf_file=exam_path,
            copy_nums=[None],
            output_paths=[intermediate_file],
            id_grid_x=student_id_widget.x,
            id_grid_y=student_id_widget.y,
            cb_data=cb_data
        )

        intermediate_file.seek(0)
        output_file = BytesIO()

        # Generate copy overlay
        generate_pdfs(
            exam_pdf_file=intermediate_file,
            copy_nums=[1559],
            output_paths=[output_file],
            exam_token="A" * token_length,
            datamatrix_x=barcode_widget.x,
            datamatrix_y=barcode_widget.y,
        )

        output_file.seek(0)

        return send_file(
            output_file,
            cache_timeout=0,
            mimetype='application/pdf')


def _exam_generate_data(exam):
    """ Retrieve data necessary to generate exam PDFs

    Parameters
    ----------
    exam : Exam
        The exam to retrieve the data for

    Returns
    -------
    exam_dir : path
        Directory with the exam data
    student_id_widget : ExamWidget
        The student id widget
    barcode_widget : ExamWidget
        The barcode widget
    exam_path : path
        The path to the exam PDF file
    cb_data : list of tuples
        List of tuples with checkbox data, each tuple represented as (x, y, page, label)
    """
    exam_dir = _get_exam_dir(exam.id)

    student_id_widget = next(
        widget
        for widget
        in exam.widgets
        if widget.name == 'student_id_widget'
    )

    barcode_widget = next(
        widget
        for widget
        in exam.widgets
        if widget.name == 'barcode_widget'
    )

    exam_path = os.path.join(exam_dir, 'exam.pdf')

    cb_data = checkboxes(exam)

    return exam_dir, student_id_widget, barcode_widget, exam_path, cb_data
