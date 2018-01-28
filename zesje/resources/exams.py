""" REST api for exams page """

from flask import abort
from flask_restful import Resource, reqparse

from pony import orm

from models import db, Exam

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


        yaml_helper.load(args['yaml'])

        version, exam_name, qr, widgets = yaml_helper.parse(yml)

        return {
        }


""" 
        # If there is already yaml for this exam, load it now so we can
        # compute a diff later
        existing_exam_data = get_exam_data(exam_name)

        if existing_exam_data:
            existing_yml_version, *_, existing_widgets = existing_exam_data
            if not all(v == 1 for v in (version, existing_yml_version)):
                raise ValueError('Exam data for {} already exists, and updating it requires both the old '
                                'and new YAML to be version 1'.format(exam_name))
            if not existing_widgets.shape == widgets.shape:
                raise ValueError('Exam data for {} already exists, and contains a different number of '


        
        
        print("Adding exam to database")
        
        try:
            if existing_exam_data:
                db.update_exam(exam_name, yaml_filename)
                print("Updated problem names for {}".format(exam_name))
            else:
                db.add_exam(yaml_filename)
                print("Added exam {} to database".format(exam_name))
            os.makedirs(exam_name + '_data', exist_ok=True)
        except Exception as exc:
            print("Failed to add exam to database")
            return
        finally:
            # XXX: use of global variables
            # update list of exams
            print("Metadata imported successfully")

"""