from flask_restful import Resource, reqparse

from werkzeug.datastructures import FileStorage
import pandas as pd
from io import BytesIO
from enum import Enum

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
            if (s := Student.query.get(student_id)) is None:
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

        student = Student(id=args.studentID,
                          first_name=args.firstName,
                          last_name=args.lastName,
                          email=args.email or None)

        result, reason = _add_or_update_student(student)

        if result == Result.UPDATED or Result.ADDED:
            db.session.commit()

        if result == Result.ERROR:
            return dict(status=400, message=reason), 400

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
            # Disable the NaN filter to allow for empty email fields
            df = pd.read_csv(BytesIO(args['csv'].read()), na_filter=False)
        except Exception:
            return dict(message='Uploaded file is not CSV'), 400

        results = []
        errors = []
        for _, row in df.iterrows():
            student = _row_to_student(row)

            if student is None:
                results.append(Result.ERROR)
                full_row = ', '.join([str(c) for c in row.values])
                errors.append(f'The following row has an incorrect format: {full_row}')

            else:
                result, reason = _add_or_update_student(student)
                results.append(result)

                if result == Result.ERROR:
                    errors.append(reason)

        # All rows failed to process
        if len(errors) == len(results):
            message = ('All the rows failed to process, '
                       'CSV is not in the correct format: '
                       'did you export it from Brightspace?')
            return dict(message=message), 400

        # At least one student was added to the database
        db.session.commit()

        return {
            'added': results.count(Result.ADDED),
            'updated': results.count(Result.UPDATED),
            'identical': results.count(Result.IDENTICAL),
            'failed': results.count(Result.ERROR),
            'errors': errors
        }


def _row_to_student(row):
    try:
        # Brightspace includes instructors in the course list,
        # and these might not have student numbers. (If they
        # do then they will be added to the student list).
        content = dict(id=int(str(row['OrgDefinedId']).replace('#', '')),
                       first_name=row['First Name'],
                       last_name=row['Last Name'],
                       email=row['Email'] or None)
    except ValueError:
        return None

    return Student(**content)


class Result(Enum):
    ERROR = -1
    IDENTICAL = 0
    UPDATED = 1
    ADDED = 2


def _add_or_update_student(student):
    """Add or update a student from a Student instance

    Returns
    -------
    result : Result
        Whether a new student was added, updated, an identical
        student was present or an error happened
    reason : str
        A description of what happened when there was
        an error, else an empty string
    """

    student_in_db = None

    if student.email:
        student_same_mail = Student.query.filter(Student.email == student.email).one_or_none()
        if student_same_mail:
            if student_same_mail.id == student.id:
                # The student with the same email is the one we are updating
                student_in_db = student_same_mail
            else:
                # Another student is already present with the same email
                return Result.ERROR, (
                    'Could not add or update student #{student_id}. ' +
                    'Another student (#{other_id}, {other_first} {other_last}) already has the same email.'
                ).format(student_id=student.id, other_id=student_same_mail.id,
                         other_first=student_same_mail.first_name, other_last=student_same_mail.last_name)

    if not student_in_db:
        student_in_db = Student.query.get(student.id)

    if not student_in_db:
        db.session.add(student)
        return Result.ADDED, ''
    elif _student_is_equal(student, student_in_db):
        return Result.IDENTICAL, ''
    else:
        student_in_db.first_name = student.first_name
        student_in_db.last_name = student.last_name
        student_in_db.email = student.email
        return Result.UPDATED, ''


def _student_is_equal(student1, student2):
    if student1.id != student2.id:
        return False
    if student1.first_name != student2.first_name:
        return False
    if student1.last_name != student2.last_name:
        return False
    return student1.email == student2.email
