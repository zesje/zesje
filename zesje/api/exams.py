import hashlib
from io import BytesIO
import os

from flask import current_app, send_file, stream_with_context, Response
from flask_restful import Resource, reqparse
from flask_restful.inputs import boolean
from werkzeug.datastructures import FileStorage
from sqlalchemy.orm import selectinload
from sqlalchemy import func

from zesje.api._helpers import _shuffle, abort
from zesje.api.problems import problem_to_data
from ..pdf_generation import exam_dir, exam_pdf_path, _exam_generate_data
from ..pdf_generation import generate_pdfs, generate_single_pdf, generate_zipped_pdfs
from ..pdf_generation import page_is_size, save_with_even_pages
from ..pdf_generation import write_finalized_exam
from ..database import db, Exam, ExamWidget, Submission, FeedbackOption, token_length, ExamLayout
from .submissions import sub_to_data


def add_blank_feedback(problems):
    """
    Add the blank feedback option to each problem.
    """
    BLANK_FEEDBACK_NAME = current_app.config['BLANK_FEEDBACK_NAME']
    for p in problems:
        db.session.add(FeedbackOption(problem_id=p.id, text=BLANK_FEEDBACK_NAME, score=0))

    db.session.commit()


def generate_exam_token(exam_id, exam_name, exam_pdf):
    hasher = hashlib.sha1()
    if exam_pdf:
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
        if (exam := Exam.query.get(exam_id)) is None:
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
        sub_count = {
            result.exam_id: result.sub_count for result in
            db.session.query(Submission.exam_id, func.count(Submission.id).label('sub_count'))
            .group_by(Submission.exam_id).all()
        }
        return [
            {
                'id': ex.id,
                'name': ex.name,
                'layout': ex.layout.name,
                'submissions': sub_count[ex.id] if ex.id in sub_count else 0,
                'finalized': ex.finalized
            }
            for ex in db.session.query(Exam).order_by(Exam.id).all()
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
                                  selectinload(Submission.solutions)).get(exam_id)

        if exam is None:
            return dict(status=404, message='Exam does not exist.'), 404

        submissions = [sub_to_data(sub) for sub in exam.submissions]

        # Sort submissions by selecting those with students assigned, then by
        # student number, then by submission id.
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
            'layout': exam.layout.name
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

        if (exam := Exam.query.get(exam_id)) is None:
            return dict(status=404, message='Exam does not exist.'), 404

        return {
            'exam_id': exam.id,
            'layout': exam.layout.name,
            'submissions': [
                {
                    'id': sub.id,
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
                } for problem in exam.problems],
            'gradeAnonymous': exam.grade_anonymous,

        }

    post_parser = reqparse.RequestParser()
    post_parser.add_argument('pdf', type=FileStorage, required=False, location='files')
    post_parser.add_argument('exam_name', type=str, required=True, location='form')
    post_parser.add_argument('layout', type=str, required=True, location='form',
                             choices=[layout.name for layout in ExamLayout])

    def post(self):
        """Add a new exam.

        Parameters
        ----------
        exam_name: str
            name for the exam
        layout: int
            the type of exam to create, one of `ExamLayout` values
        pdf : file, optional
            raw pdf file.

        Returns
        -------
        id : int
            exam ID
        """

        args = self.post_parser.parse_args()
        exam_name = args['exam_name'].strip()
        layout = args['layout']

        if not exam_name:
            return dict(status=400, message='Exam name is empty'), 400

        if layout == ExamLayout.templated.name:
            pdf_data = args['pdf']
            exam = self._add_templated_exam(exam_name, pdf_data)
        elif layout == ExamLayout.unstructured.name:
            exam = self._add_unstructured_exam(exam_name)
        else:
            return dict(status=400, message=f'Exam type {layout} is not defined'), 400

        print(f"Added exam {exam.id} (name: {exam_name}, token: {exam.token}) to database")

        return {
            'id': exam.id
        }

    def _add_templated_exam(self, exam_name, pdf_data):
        if not pdf_data:
            abort(
                400,
                message='Upload a PDF to add a templated exam.'
            )

        format = current_app.config['PAGE_FORMAT']

        if not page_is_size(pdf_data, current_app.config['PAGE_FORMATS'][format], tolerance=0.01):
            abort(
                400,
                message=f'PDF page size is not {format}.'
            )

        exam = Exam(
            name=exam_name,
            layout=ExamLayout.templated
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

        save_with_even_pages(exam.id, pdf_data)

        return exam

    def _add_unstructured_exam(self, exam_name):
        exam = Exam(
            name=exam_name,
            layout=ExamLayout.unstructured
        )

        db.session.add(exam)
        db.session.commit()  # so exam gets an id
        exam.token = generate_exam_token(exam.id, exam_name, None)
        db.session.commit()

        os.makedirs(exam_dir(exam.id), exist_ok=True)

        return exam

    put_parser = reqparse.RequestParser()
    put_parser.add_argument('finalized', type=bool, required=False)
    put_parser.add_argument('grade_anonymous', type=bool, required=False)

    def put(self, exam_id):
        if (exam := Exam.query.get(exam_id)) is None:
            return dict(status=404, message='Exam does not exist.'), 404

        args = self.put_parser.parse_args()

        if args['finalized'] is None:
            pass
        elif args['finalized']:
            add_blank_feedback(exam.problems)

            if exam.layout == ExamLayout.templated:
                write_finalized_exam(exam)

            exam.finalized = True
            db.session.commit()
            return dict(status=200, message="ok"), 200
        else:
            return dict(status=403, message='Exam can not be unfinalized'), 403

        if args['grade_anonymous'] is not None:
            changed = exam.grade_anonymous != args['grade_anonymous']
            exam.grade_anonymous = args['grade_anonymous']
            db.session.commit()
            return dict(status=200, message="ok", changed=changed), 200

        return dict(status=400, message='One of finalized or anonymous must be present'), 400

    patch_parser = reqparse.RequestParser()
    patch_parser.add_argument('name', type=str, required=True)

    def patch(self, exam_id):
        """Update the name of an existing exam.

        Parameters
        ----------
        name: str
            name for the exam
        """

        if (exam := Exam.query.get(exam_id)) is None:
            return dict(status=404, message='Exam does not exist.'), 404

        args = self.patch_parser.parse_args()
        if not (name := args['name'].strip()):
            return dict(status=400, message='Exam name is empty.'), 400

        exam.name = name
        db.session.commit()

        return dict(status=200, message='ok'), 200


class ExamSource(Resource):

    def get(self, exam_id):

        if (exam := Exam.query.get(exam_id)) is None:
            return dict(status=404, message='Exam does not exist.'), 404

        if exam.layout == ExamLayout.unstructured:
            return dict(status=404, message='Unstructured exams have no pdf.'), 404

        return send_file(
            exam_pdf_path(exam.id),
            max_age=0,
            mimetype='application/pdf')


class ExamGeneratedPdfs(Resource):

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

        if (exam := Exam.query.get(exam_id)) is None:
            return dict(status=404, message='Exam does not exist.'), 404
        if not exam.finalized:
            msg = 'Exam is not finalized.'
            return dict(status=403, message=msg), 403
        if exam.layout == ExamLayout.unstructured:
            return dict(status=404, message='Unstructured exams have no pdf.'), 404

        if copies_end < copies_start:
            msg = 'copies_end should be larger than copies_start'
            return dict(status=400, message=msg), 400
        if copies_start <= 0:
            msg = 'copies_start should be larger than 0'
            return dict(status=400, message=msg), 400

        attachment_filename = f'{exam.name}_{copies_start}-{copies_end}.{args["type"]}'
        mimetype = f'application/{args["type"]}'

        if args['type'] == 'pdf':
            output_file = BytesIO()
            generate_single_pdf(exam, copies_start, copies_end, output_file)
            output_file.seek(0)
            return send_file(
                output_file,
                max_age=0,
                download_name=attachment_filename,
                as_attachment=True,
                mimetype=mimetype)
        elif args['type'] == 'zip':
            generator = generate_zipped_pdfs(exam.id, copies_start, copies_end)
            response = Response(stream_with_context(generator), mimetype=mimetype)
            response.headers['Content-Disposition'] = f'attachment; filename="{attachment_filename}"'
            return response

        return dict(status=400, message='type must be one of ["pdf", "zip"]'), 400


class ExamPreview(Resource):

    def get(self, exam_id):
        if (exam := Exam.query.get(exam_id)) is None:
            return dict(status=404, message='Exam does not exist.'), 404
        if exam.layout == ExamLayout.unstructured:
            return dict(status=404, message='Unstructured exams have no pdf.'), 404

        exam_dir, student_id_widget, barcode_widget, exam_path, cb_data = _exam_generate_data(exam)

        # Generate generic overlay
        _, intermediate_file = next(generate_pdfs(
            exam_pdf_file=exam_path,
            copy_nums=[None],
            id_grid_x=student_id_widget.x,
            id_grid_y=student_id_widget.y,
            cb_data=cb_data
        ))

        # Generate copy overlay
        _, output_file = next(generate_pdfs(
            exam_pdf_file=intermediate_file,
            copy_nums=[1559],
            exam_token="A" * token_length,
            datamatrix_x=barcode_widget.x,
            datamatrix_y=barcode_widget.y,
        ))

        return send_file(
            output_file,
            cache_timeout=0,
            mimetype='application/pdf')
