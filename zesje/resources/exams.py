""" REST api for exams page """

from flask import abort
from flask_restful import Resource, reqparse

from pony import orm

from models import db, Exam

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

        print(args['yaml'])

        return {
        }










"""


@app.route('/exams', methods=['POST'])
def post_new_yaml():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            print('No file part')
            abort(400)
        file = request.files['file']
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            print('No selected file')
            abort(400)
        if file:
            try:

                yml = yaml.safe_load(file.read())

                try:
                    yml = db.clean_yaml(yml)  # attempt to clean
                except Exception:
                    pass  # if the YAML is not valid parsing will raise anyway
                version, exam_name, qr, widgets = db.parse_yaml(yml)
                
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
                                        'exam problems than {}'.format(exam_name, yaml_upload.filename))
            except ValueError as exc:
                print(str(exc))
                abort(400)
            except Exception as exc:
                print("Invalid metadata")
                print(exc)
                abort(400)

            # save yaml
            yaml_filename = exam_name + '.yml'
            print("Saving " + yaml_filename)
            try:
                with open(yaml_filename, 'w') as f:
                    f.write(yaml.safe_dump(yml, default_flow_style=False))
            except Exception:
                print("Failed to save " + yaml_filename)
                abort(400)
            
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
            