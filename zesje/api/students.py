from flask_restful import Resource, reqparse

from pony import orm
from werkzeug.datastructures import FileStorage
import pandas as pd
from io import BytesIO

from ..database import Student


class Students(Resource):
    """Getting a list of students."""

    @orm.db_session
    def get(self, student_id=None):
        """get all students for the course.

         Parameters
        ----------
        student_id : int, optional
            The ID of the student, often the studentnumber but mainly used as unique identifier

        Returns
        -------
        If a valid 'student_id' is provided the single instance of the student will be returned:
            id: int
            first_name: str
            last_name: str
            email: str

        If no student_id is provided the entire list of students will be returned.
        """

        if student_id is not None:
            s = Student.get(id=student_id)
            if not s:
                return dict(status=404, message='Student not found'), 404
            return {
                'id': s.id,
                'firstName': s.first_name,
                'lastName': s.last_name,
                'email': s.email,
            }

        return [
            {
                'id': s.id,
                'firstName': s.first_name,
                'lastName': s.last_name,
                'email': s.email,
            }
            for s in Student.select()
        ]

    put_parser = reqparse.RequestParser()
    put_parser.add_argument('studentID', type=int, required=True)
    put_parser.add_argument('firstName', type=str, required=True)
    put_parser.add_argument('lastName', type=str, required=True)
    put_parser.add_argument('email', type=str, required=False)

    @orm.db_session
    def put(self, student_id=None):
        """Insert or update an existing student

        Expects a json payload in the format::

            {
                "studentID": int,
                "firstName": str,
                "lastName": str,
                "email": str OR null - this value is optional and may be empty, but must be unique
            }

        Parameters
        ----------
        None. 'student_id' will be ignored.

        Returns
        -------
        instance of student in JSON format:
            studentID: int
            firstName: str
            lastName: str
            email: str OR null

        """

        args = self.put_parser.parse_args()

        student = Student.get(id=args.studentID)
        if not student:
            student = Student(id=args.studentID,
                              first_name=args.firstName,
                              last_name=args.lastName,
                              email=args.email or None)
        else:
            student.set(id=args.studentID,
                        first_name=args.firstName,
                        last_name=args.lastName,
                        email=args.email or None)
        orm.commit()

        return {
            'studentID': student.id,
            "firstName": student.first_name,
            "lastName": student.last_name,
            "email": student.email
        }

    post_parser = reqparse.RequestParser()
    post_parser.add_argument('csv', type=FileStorage, required=True,
                             location='files')

    @orm.db_session
    def post(self):
        """Upload a CSV file and add/update the students.

        Parameters
        ----------
        csv : FileStorage
            The CSV file. It should have the following columns:
             - "OrgDefinedId" (student id)
             - "First Name"
             - "Last Name"
             - "Email" (optional)

        Returns
        -------
        The number of *new* students that were added.
        """
        args = self.post_parser.parse_args()
        try:
            df = pd.read_csv(BytesIO(args['csv'].read()))
        except Exception:
            return dict(message='Uploaded file is not CSV'), 400

        try:
            added_students = sum(_add_or_update_student(row)
                                 for _, row in df.iterrows())
        except Exception as e:
            message = ('Uploaded CSV is not in the correct format: '
                       'did you export it from Brightspace? '
                       'The error was: ' + str(e))
            return dict(message=message), 400

        return added_students


def _add_or_update_student(row):
    """Add or update a student from a CSV row.

    Returns whether a new student was added
    (False if the student was already present, or
    if there was an error processing the row).
    """
    content = dict(id=row['OrgDefinedId'][1:],
                   first_name=row['First Name'],
                   last_name=row['Last Name'],
                   email=row['Email'] or None)
    try:
        # Brightspace includes instructors in the course list,
        # and these might not have student numbers. (If they
        # do then they will be added to the student list).
        student = Student.get(id=content['id'])
    except ValueError:
        return False
    if not student:
        Student(**content)
        return True
    else:
        student.set(**content)
        return False
