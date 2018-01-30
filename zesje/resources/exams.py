""" REST api for exams page """
import os

from flask import abort
from flask_restful import Resource, reqparse

from pony import orm

from models import db, Exam, Problem, FeedbackOption

from helpers import yaml_helper

parser = reqparse.RequestParser()
parser.add_argument('yaml', type=str, required=True)

class Exams(Resource):
    """ Exam storage and processing, including the YAML that stores the metadata """

    @orm.db_session
    def get(self):
        """get list of uploaded exams and their yaml.

        Returns
        -------
        list of:
            name: str
            yaml: str
        """

        return [
                {
                    'name' : ex.name,
                    'yaml' : ex.yaml_path,
                }
                for ex in Exam.select()
        ]

    @orm.db_session
    def post(self):
        """ Post a new yaml config
        Will overwrite existing yaml if the name is the same

        Returns
        _______
        [200] if okay
        """

        args = parser.parse_args()

        yml = yaml_helper.load(args['yaml'])

        version, exam_name, qr, widgets = yaml_helper.parse(yml)

        
        existing_exam = Exam.get(name=exam_name)
        if existing_exam is None:
            os.makedirs(exam_name + '_data', exist_ok=True)

            exam = Exam(name=exam_name, yaml_path=exam_name + '.yml')

            # Default feedback (maybe factor out eventually).
            feedback_options = ['Everything correct',
                                'No solution provided']

            for name in widgets.index:
                if name == 'studentnr':
                    continue
                p = Problem(name=name, exam=exam)
                for fb in feedback_options:
                    FeedbackOption(text=fb, problem=p)

            yaml_helper.save(yml)
            print("Added exam {} to database".format(exam_name))
        else:
            existing_yml = yaml_helper.read(existing_exam.yaml_path)
            existing_version, *_, existing_widgets = yaml_helper.parse(existing_yml)
            if not all(v == 1 for v in (version, existing_version)):
                raise ValueError('Exam data for {} already exists, and updating it requires both the old '
                                'and new YAML to be version 1'.format(exam_name))
            if not existing_widgets.shape == widgets.shape:
                raise ValueError('Exam data for {} already exists, and contains a different number of '
                                 'exam problems than the old version'.format(exam_name))
            
            #db.update_exam(exam_name, yaml_filename)

            print("Updated problem names for {}".format(exam_name))

        os.makedirs(exam_name + '_data', exist_ok=True)

        return {
        }
