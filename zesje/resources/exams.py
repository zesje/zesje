""" REST api for exams page """
import os

from flask import abort, current_app as app
from flask_restful import Resource, reqparse
from werkzeug.datastructures import FileStorage

from pony import orm

from ..helpers import yaml_helper
from ..models import db, Exam, Problem, FeedbackOption
from ..helpers import db_helper



class Exams(Resource):
    """ Exam storage and processing, including the YAML that stores the metadata """

    @orm.db_session
    def get(self):
        """get list of uploaded exams and their yaml.

        Returns
        -------
        list of:
            id: int
            name: str
        """
        return [
            {
                'id': ex.id,
                'name' : ex.name,
            }
            for ex in Exam.select().order_by(Exam.id)
        ]

    @orm.db_session
    def post(self):
        """ Post a new yaml config
        Will overwrite existing yaml if the name is the same

        Returns
        -------
        id: int
        name: str
        yaml: str
        """
        parser = reqparse.RequestParser()
        parser.add_argument('yaml', type=FileStorage, required=True,
                            location='files')
        args = parser.parse_args()

        yml = yaml_helper.load(args['yaml'])

        version, exam_name, qr, widgets = yaml_helper.parse(yml)
        
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
