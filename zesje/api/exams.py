import itertools
import os
import zipfile
from io import BytesIO
from tempfile import TemporaryFile

from flask import current_app as app, send_file, request
from flask_restful import Resource, reqparse
from werkzeug.datastructures import FileStorage
from sqlalchemy.orm import selectinload

from ..pdf_generation import generate_pdfs, output_pdf_filename_format, join_pdfs, page_is_size
from ..database import db, Exam, ExamWidget, Submission

PAGE_FORMATS = {
    "A4": (595.276, 841.89),
    "US letter": (612, 792),
}


def _get_exam_dir(exam_id):
    return os.path.join(
        app.config['DATA_DIRECTORY'],
        f'{exam_id}_data',
    )


class Exams(Resource):

    def get(self, exam_id=None):
        if exam_id:
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
            # Delete any scans that were wrongly uploaded to this exam
            for scan in exam.scans:
                db.session.delete(scan)

            for widget in exam.widgets:
                db.session.delete(widget)

            for problem in exam.problems:
                for fb_option in problem.feedback_options:
                    db.session.delete(fb_option)
                db.session.delete(problem.widget)
                db.session.delete(problem)

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

        submissions = [
                {
                    'id': sub.copy_number,
                    'student': {
                            'id': sub.student.id,
                            'firstName': sub.student.first_name,
                            'lastName': sub.student.last_name,
                            'email': sub.student.email
                    } if sub.student else None,
                    'validated': sub.signature_validated,
                    'problems': [
                        {
                            'id': sol.problem.id,
                            'graded_by': {
                                'id': sol.graded_by.id,
                                'name': sol.graded_by.name
                            } if sol.graded_by else None,
                            'graded_at': sol.graded_at.isoformat() if sol.graded_at else None,
                            'feedback': [
                                fb.id for fb in sol.feedback
                            ],
                            'remark': sol.remarks if sol.remarks else ""
                        } for sol in sub.solutions  # Sorted by sol.problem_id
                    ],
                } for sub in exam.submissions
        ]
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
            'problems': [
                {
                    'id': prob.id,
                    'name': prob.name,
                    'feedback': [
                        {
                            'id': fb.id,
                            'name': fb.text,
                            'description': fb.description,
                            'score': fb.score,
                            'used': len(fb.solutions)
                        }
                        for fb
                        in prob.feedback_options  # Sorted by fb.id
                    ],
                    'page': prob.widget.page,
                    'widget': {
                        'id': prob.widget.id,
                        'name': prob.widget.name,
                        'x': prob.widget.x,
                        'y': prob.widget.y,
                        'width': prob.widget.width,
                        'height': prob.widget.height,
                    },
                    'graded': any([sol.graded_by is not None for sol in prob.solutions])
                } for prob in exam.problems  # Sorted by prob.id
            ],
            'widgets': [
                {
                    'id': widget.id,
                    'name': widget.name,
                    'x': widget.x,
                    'y': widget.y,
                } for widget in exam.widgets  # Sorted by widget.id
            ],
            'finalized': exam.finalized,
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

        format = app.config.get('PAGE_FORMAT', 'A4')

        if not page_is_size(pdf_data, PAGE_FORMATS[format], tolerance=0.01):
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

        exam_dir = _get_exam_dir(exam.id)
        pdf_path = os.path.join(exam_dir, 'exam.pdf')

        os.makedirs(exam_dir, exist_ok=True)

        pdf_data.save(pdf_path)

        print(f"Added exam {exam.id} (name: {exam_name}, token: {exam.token}) to database")

        return {
            'id': exam.id
        }

    def put(self, exam_id, attr):
        if attr == 'finalized':
            exam = Exam.query.get(exam_id)
            if exam is None:
                return dict(status=404, message='Exam does not exist.'), 404

            bodyStr = request.data.decode('utf-8')
            if bodyStr == 'true':
                exam.finalized = True
                db.session.commit()
            elif bodyStr == 'false':
                if exam.finalized:
                    return dict(status=403, message=f'Exam already finalized'), 403
            else:
                return dict(status=400, message=f'Body should be "true" or "false"'), 400
            return dict(status=200, message="ok"), 200
        else:
            return dict(status=400, message=f'Attribute {attr} not allowed'), 400


class ExamSource(Resource):

    def get(self, exam_id):

        exam = Exam.query.get(exam_id)

        if exam is None:
            return dict(status=404, message='Exam does not exist.'), 404

        exam_dir = _get_exam_dir(exam.id)

        return send_file(
            os.path.join(exam_dir, 'exam.pdf'),
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
                output_pdf_filename_format.format(copy_num))
            for copy_num
            in copy_nums
        ]
        return pdf_paths, copy_nums

    def _generate_exam_pdfs(self, exam, pdf_paths, copy_nums):
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

        generated_pdfs_dir = self._get_generated_exam_dir(exam_dir)
        os.makedirs(generated_pdfs_dir, exist_ok=True)

        generate_pdfs(
            exam_path,
            exam.token,
            copy_nums,
            pdf_paths,
            student_id_widget.x, student_id_widget.y,
            barcode_widget.x, barcode_widget.y
        )

    post_parser = reqparse.RequestParser()
    post_parser.add_argument('copies_start', type=int, required=True)
    post_parser.add_argument('copies_end', type=int, required=True)

    def post(self, exam_id):
        """Generates the exams with corner markers and Widgets.

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

        args = self.post_parser.parse_args()

        copies_start = args.get('copies_start')
        copies_end = args.get('copies_end')

        exam = Exam.query.get(exam_id)
        if exam is None:
            return dict(status=404, message='Exam does not exist.'), 404

        exam_dir = _get_exam_dir(exam_id)
        generated_pdfs_dir = self._get_generated_exam_dir(exam_dir)

        if not exam.finalized:
            msg = f'Exam is not finalized.'
            return dict(status=403, message=msg), 403
        if copies_start is None or copies_end is None:
            msg = f'Missing parameters and/or "copies_start", "copies_end"'
            return dict(status=400, message=msg), 400
        if copies_end < copies_start:
            msg = f'copies_end should be larger than copies_start'
            return dict(status=400, message=msg), 400
        if copies_start <= 0:
            msg = f'copies_start should be larger than 0'
            return dict(status=400, message=msg), 400

        pdf_paths, copy_nums = self._get_paths_for_range(generated_pdfs_dir, copies_start, copies_end)

        generate_selectors = [not os.path.exists(pdf_path) for pdf_path in pdf_paths]
        pdf_paths = itertools.compress(pdf_paths, generate_selectors)
        copy_nums = itertools.compress(copy_nums, generate_selectors)

        self._generate_exam_pdfs(exam, pdf_paths, copy_nums)

        return {
            'success': True
        }

    get_parser = reqparse.RequestParser()
    get_parser.add_argument('copies_start', type=int, required=True)
    get_parser.add_argument('copies_end', type=int, required=True)
    get_parser.add_argument('type', type=str, required=True)

    def get(self, exam_id):
        args = self.get_parser.parse_args()

        copies_start = args['copies_start']
        copies_end = args['copies_end']

        exam = Exam.query.get(exam_id)
        if exam is None:
            return dict(status=404, message='Exam does not exist.'), 404

        exam_dir = _get_exam_dir(exam_id)
        generated_pdfs_dir = self._get_generated_exam_dir(exam_dir)

        output_file = TemporaryFile()

        pdf_paths, copy_nums = self._get_paths_for_range(generated_pdfs_dir, copies_start, copies_end)

        for pdf_path in pdf_paths:
            if not os.path.exists(pdf_path):
                msg = f'One or more exams in range have not been generated (yet)'
                return dict(status=400, message=msg), 400

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

        output_file = BytesIO()

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

        generate_pdfs(
            exam_path,
            exam.token[:5] + 'PREVIEW',
            [1519],
            [output_file],
            student_id_widget.x, student_id_widget.y,
            barcode_widget.x, barcode_widget.y
        )

        output_file.seek(0)

        return send_file(
            output_file,
            cache_timeout=0,
            mimetype='application/pdf')
