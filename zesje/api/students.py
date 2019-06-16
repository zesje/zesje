from flask_restful import Resource, reqparse

from werkzeug.datastructures import FileStorage
import pandas as pd
from io import BytesIO

from ..database import db, Student


class Students(Resource):
    """Getting a list of students."""

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
            s = Student.query.get(student_id)
            if s is None:
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
            for s in Student.query.all()
        ]

    put_parser = reqparse.RequestParser()
    put_parser.add_argument('studentID', type=int, required=True)
    put_parser.add_argument('firstName', type=str, required=True)
    put_parser.add_argument('lastName', type=str, required=True)
    put_parser.add_argument('email', type=str, required=False)

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

        student = Student.query.get(args.studentID)

        # Check if another student with same email is already present
        # and that it is not the student we are updating
        if args.email and (not student or student.email != args.email):
            student_same_mail = Student.query.filter(Student.email == args.email).one_or_none()
            if student_same_mail:
                return dict(status=400, message=(
                    '''Could not add or update student #{student_id}.
                    Another student (#{other_id}, {other_first} {other_last}) already has the same email.'''
                    .format(student_id=args.studentID, other_id=student_same_mail.id,
                            other_first=student_same_mail.first_name, other_last=student_same_mail.last_name))), 400

        if student is None:
            student = Student(id=args.studentID,
                              first_name=args.firstName,
                              last_name=args.lastName,
                              email=args.email or None)
            db.session.add(student)
        else:
            student.id = args.studentID
            student.first_name = args.firstName
            student.last_name = args.lastName
            student.email = args.email or None

        db.session.commit()

        return {
            'studentID': student.id,
            "firstName": student.first_name,
            "lastName": student.last_name,
            "email": student.email
        }

    post_parser = reqparse.RequestParser()
    post_parser.add_argument('csv', type=FileStorage, required=True,
                             location='files')

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
            print(e)
            message = ('Uploaded CSV is not in the correct format: '
                       'did you export it from Brightspace? '
                       'The error was: ' + str(type(e)) + ": " + str(e))
            return dict(message=message), 400

        db.session.commit()

        return added_students


def _add_or_update_student(row):
    """Add or update a student from a CSV row.

    Returns whether a new student was added
    (False if the student was already present, or
    if there was an error processing the row).
    """
    content = dict(id=row['OrgDefinedId'].replace('#', ''),
                   first_name=row['First Name'],
                   last_name=row['Last Name'],
                   email=row['Email'] or None)
    try:
        # Brightspace includes instructors in the course list,
        # and these might not have student numbers. (If they
        # do then they will be added to the student list).
        content['id'] = int(str(content['id']).replace('#', ''))
        student = Student.query.get(content['id'])
    except ValueError:
        return False
    if student is None:
        db.session.add(Student(**content))
        return True
    else:
        student.id = content['id']
        student.first_name = content['first_name']
        student.last_name = content['last_name']
        student.email = content['email']
        return False
