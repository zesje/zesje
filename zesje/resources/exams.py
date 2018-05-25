import os
import json

from flask import abort, current_app as app, send_file
from flask_restful import Resource, reqparse
from werkzeug.datastructures import FileStorage

from pony import orm

from ..helpers import yaml_helper, db_helper, image_helper
from ..models import db, Exam, Problem, FeedbackOption
from ._helpers import required_string


class ExamConfig(Resource):

    @orm.db_session
    def get(self, exam_id):
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
                        } for fb in prob.feedback_options.order_by(lambda f: f.id)
                    ]
                } for prob in exam.problems.order_by(lambda p: p.id)
            ],
            'widgets': [
                {
                    'id': widget.id,
                    'data': widget.data.decode("utf-8")
                } for widget in exam.widgets.order_by(lambda w: w.id)
            ],
        }

    patch_parser = reqparse.RequestParser()
    required_string(patch_parser, 'yaml')

    @orm.db_session
    def patch(self, exam_id):
        """Update a single exam's config

        URL Parameters
        --------------
        exam_id : int
            exam ID

        Parameters
        ----------
        yaml : str
            processed YAML config
        """
        args = self.patch_parser.parse_args()

        exam = Exam[exam_id]

        data_dir = app.config['DATA_DIRECTORY']
        yaml_filename = exam.name + '.yml'
        yaml_abspath = os.path.join(data_dir, yaml_filename)
        existing_yml = yaml_helper.read(yaml_abspath)
        new_yml = yaml_helper.load(args['yaml'])

        db_helper.update_exam(exam, existing_yml, new_yml)

        yaml_helper.save(new_yml, yaml_abspath)

        print("Updated problem names for {}".format(exam.name))


class Exams(Resource):

    @orm.db_session
    def get_pdf(exam_id):

        exam = Exam[exam_id]

        data_dir = app.config['DATA_DIRECTORY']
        exam_dir = os.path.join(data_dir, exam.name + '_data')

        return send_file(
            os.path.join(exam_dir, 'exam.pdf'),
            mimetype='application/pdf')

    @orm.db_session
    def check_validity(exam_id):

        exam = Exam[exam_id]

        data_dir = app.config['DATA_DIRECTORY']
        pdf_path = os.path.join(data_dir, exam.name + '_data', 'exam.pdf')

        result = image_helper.check_enough_blankspace(pdf_path)

        return json.dumps(result)

    @orm.db_session
    def get(self):
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
                'name' : ex.name,
                'submissions': ex.submissions.count()
            }
            for ex in Exam.select().order_by(Exam.id)
        ]

    post_parser = reqparse.RequestParser()
    post_parser.add_argument('pdf', type=FileStorage, required=True, location='files')
    post_parser.add_argument('exam_name', type=str, required=True, location='form')

    @orm.db_session
    def post(self):
        """Add a new exam.

        Will error if an existing exam exists with the same name.

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

        exam = Exam.get(name=exam_name)

        if exam is None:
            exam = Exam(name=exam_name)

            data_dir = app.config['DATA_DIRECTORY']
            exam_dir = os.path.join(data_dir, exam_name + '_data')
            pdf_path = os.path.join(exam_dir, 'exam.pdf')

            os.makedirs(exam_dir, exist_ok=True)
            db.commit()

            pdf_data.save(pdf_path)

            # Default feedback (maybe factor out eventually).
            feedback_options = ['Everything correct',
                                'No solution provided']

            print("Added exam {} to database".format(exam.name))
        else:
            msg = "Exam with name {} already exists".format(exam.name)
            return dict(status=400, message=msg), 400

        return {
            'id': exam.id
        }
