import os
import glob
import zipfile
from io import BytesIO
import datetime

from flask import current_app as app, abort, send_file
from flask_restful import Resource, reqparse
from werkzeug.datastructures import FileStorage

from pony import orm

from ..helpers.pdf_generation_helper import generate_pdfs, \
    output_pdf_filename_format, join_pdfs


from ..models import db, Exam, ExamWidget


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

    @orm.db_session
    def _get_all(self):
        """get list of uploaded exams and their yaml.

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
                'submissions': ex.submissions.count()
            }
            for ex in Exam.select().order_by(Exam.id)
        ]

    @orm.db_session
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
        submissions: int
            Number of submissions
        yaml : str
            YAML config
        """
        exam = Exam[exam_id]

        return {
            'id': exam_id,
            'name': exam.name,
            'submissions':
            [
                {
                    'id': sub.copy_number,
                    'student':
                        {
                            'id': sub.student.id,
                            'firstName': sub.student.first_name,
                            'lastName': sub.student.last_name,
                            'email': sub.student.email
                        } if sub.student else None,
                    'validated': sub.signature_validated,
                    'problems':
                    [
                        {
                            'id': sol.problem.id,
                            'graded_by': sol.graded_by,
                            'graded_at': sol.graded_at.isoformat() if sol.graded_at else None,
                            'feedback': [
                                fb.id for fb in sol.feedback
                            ],
                            'remark': sol.remarks
                        } for sol in sub.solutions.order_by(lambda s: s.problem.id)
                    ]
                } for sub in exam.submissions.order_by(lambda s: s.copy_number)
            ],
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
                            'used': fb.solutions.count()
                        }
                        for fb
                        in prob.feedback_options.order_by(lambda f: f.id)
                    ],
                    'page': prob.page,
                    'widget': {
                        'id': prob.widget.id,
                        'name': prob.widget.name,
                        'x': prob.widget.x,
                        'y': prob.widget.y,
                        'width': prob.widget.width,
                        'height': prob.widget.height,
                    },
                } for prob in exam.problems.order_by(lambda p: p.id)
            ],
            'widgets': [
                {
                    'id': widget.id,
                    'name': widget.name,
                    'x': widget.x,
                    'y': widget.y,
                } for widget in exam.widgets.order_by(lambda w: w.id)
            ]
        }

    post_parser = reqparse.RequestParser()
    post_parser.add_argument('pdf', type=FileStorage, required=True, location='files')
    post_parser.add_argument('exam_name', type=str, required=True, location='form')

    @orm.db_session
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

        db.commit()  # so exam gets an id

        exam_dir = _get_exam_dir(exam.id)
        pdf_path = os.path.join(exam_dir, 'exam.pdf')

        os.makedirs(exam_dir, exist_ok=True)

        pdf_data.save(pdf_path)

        print(f"Added exam {exam.id} (name: {exam_name}, token: {exam.token}) to database")

        return {
            'id': exam.id
        }


class ExamSource(Resource):

    @orm.db_session
    def get(self, exam_id):

        exam = Exam[exam_id]

        exam_dir = _get_exam_dir(exam.id)

        return send_file(
            os.path.join(exam_dir, 'exam.pdf'),
            mimetype='application/pdf')


class ExamGeneratedPdfs(Resource):

    get_parser = reqparse.RequestParser()
    get_parser.add_argument('type', type=str, required=True, location='args')

    @orm.db_session
    def get(self, exam_id, copy_num=None):

        exam_dir = _get_exam_dir(exam_id)
        generated_pdfs_dir = os.path.join(
            exam_dir,
            'generated_pdfs'
        )

        if (not os.path.exists(generated_pdfs_dir)):
            abort(404)

        if copy_num is None:
            # get all (zip)
            # TODO: use query to define ranges

            args = self.get_parser.parse_args()

            exam = Exam[exam_id]
            now_str = datetime.datetime.now().strftime("%Y-%m-%d_%H:%M")

            if args['type'] == 'pdf':
                out_pdf_path = os.path.join(generated_pdfs_dir, 'all.pdf')

                pdf_count = len(glob.glob1(
                    generated_pdfs_dir,
                    '[0-9][0-9][0-9][0-9][0-9].pdf'))

                join_pdfs(
                    generated_pdfs_dir,
                    out_pdf_path,
                    pdf_count,
                )

                return send_file(
                    out_pdf_path,
                    cache_timeout=0,
                    attachment_filename=f'{exam.name}_{now_str}.pdf',
                    as_attachment=True,
                    mimetype='application/pdf')

            elif args['type'] == 'zip':

                memory_file = BytesIO()
                with zipfile.ZipFile(memory_file, 'w') as zf:
                    for root, dirs, files in os.walk(generated_pdfs_dir):
                        for file in files:
                            zf.write(
                                os.path.join(root, file),
                                file)

                memory_file.seek(0)

                return send_file(
                    memory_file,
                    cache_timeout=0,
                    attachment_filename=f'{exam.name}_{now_str}.zip',
                    as_attachment=True,
                    mimetype='application/zip')
            else:
                # needs either zip or pdf
                abort(400)

        else:
            # single file requested, we can directly send
            pdf_path = os.path.join(
                generated_pdfs_dir,
                output_pdf_filename_format.format(copy_num))

            if (not os.path.exists(pdf_path)):
                abort(404)

            return send_file(
                pdf_path,
                cache_timeout=0,
                mimetype='application/pdf')

    post_parser = reqparse.RequestParser()
    post_parser.add_argument('copies', type=int, required=True)

    @orm.db_session
    def post(self, exam_id):

        args = self.post_parser.parse_args()

        exam = Exam.get(id=exam_id)
        if (exam is None):
            abort(404)

        exam_dir = _get_exam_dir(exam_id)

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

        pdf_path = os.path.join(exam_dir, 'exam.pdf')

        pdf_out_dir = os.path.join(exam_dir, 'generated_pdfs')
        os.makedirs(pdf_out_dir, exist_ok=True)

        for f in glob.glob1(pdf_out_dir,
                            '[0-9][0-9][0-9][0-9][0-9].pdf'):
            os.remove(os.path.join(pdf_out_dir, f))

        generate_pdfs(
            pdf_path,
            'ABCDEFGHIJKL',
            pdf_out_dir,
            args['copies'],
            student_id_widget.x, student_id_widget.y,
            barcode_widget.x, barcode_widget.y
        )

        return {
            'success': True
        }
