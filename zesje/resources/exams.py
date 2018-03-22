import os

from flask import abort, current_app as app
from flask_restful import Resource, reqparse
from werkzeug.datastructures import FileStorage

from pony import orm

from ..helpers import yaml_helper, db_helper
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
        yaml : str
            YAML config
        """
        exam = Exam[exam_id]

        data_dir = app.config['DATA_DIRECTORY']
        with open(os.path.join(data_dir, exam.yaml_path)) as f:
            yml = f.read()

        return {
            'id': exam_id,
            'name': exam.name,
            'yaml': yml
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
    def get(self):
        """get list of uploaded exams and their yaml.

        Returns
        -------
        list of:
            id : int
                exam name
            name : str
                exam ID
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
    post_parser.add_argument('yaml', type=FileStorage, required=True,
                             location='files')

    @orm.db_session
    def post(self):
        """Add a new exam.

        Will overwrite an existing exam if the name is the same.

        Parameters
        ----------
        yaml : file
            potentially unprocessed exam config.

        Returns
        -------
        id : int
            exam ID
        name : str
            exam name
        yaml : str
            processed config
        """

        args = self.post_parser.parse_args()

        try:
            yml = yaml_helper.load(args['yaml'])
            version, exam_name, qr, widgets = yaml_helper.parse(yml)
        except Exception:
            return dict(message='Invalid config file'), 400
        
        data_dir = app.config['DATA_DIRECTORY']
        yaml_filename = exam_name + '.yml'
        yaml_abspath = os.path.join(data_dir, yaml_filename)
        exam_dir = os.path.join(data_dir, exam_name + '_data')
        exam = Exam.get(name=exam_name)

        if exam is None:
            os.makedirs(exam_dir, exist_ok=True)

            exam = Exam(name=exam_name, yaml_path=exam_name + '.yml')
            db.commit()

            # Default feedback (maybe factor out eventually).
            feedback_options = ['Everything correct',
                                'No solution provided']

            for name in widgets.index:
                if name == 'studentnr':
                    continue
                p = Problem(name=name, exam=exam)
                for fb in feedback_options:
                    FeedbackOption(text=fb, problem=p)

            yaml_helper.save(yml, yaml_abspath)
            print("Added exam {} to database".format(exam_name))
        else:
            assert yaml_abspath == os.path.join(data_dir, exam.yaml_path)
            existing_yml = yaml_helper.read(yaml_abspath)
            db_helper.update_exam(exam, existing_yml, yml)
            yaml_helper.save(yml, yaml_abspath)
            print("Updated problem names for {}".format(exam_name))

        with open(yaml_abspath) as f:
            yml = f.read()

        return {
            'id': exam.id,
            'name': exam.name,
            'yaml': yml,
        }
