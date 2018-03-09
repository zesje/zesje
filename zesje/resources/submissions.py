from flask_restful import Resource, reqparse
from pony import orm

from ..models import Exam, Submission, Student

class Submissions(Resource):
    """Getting a list of submissions, and assigning students to them."""

    @orm.db_session
    def get(self, exam_id, submission_id=None):
        """get submissions for the given exam, ordered by copy number.

        Parameters
        ----------
        exam_id : int
        submission_id : int, optional
            The copy number of the submission. This uniquely identifies
            the submission *within a given exam*.

        Returns
        -------
        If 'submission_id' not provided provides a single instance of
        (otherwise a list of):
            copyID: int
            studentID: int or null
                Student that completed this submission, null if not assigned.
            validated: bool
                True if the assigned student has been validated by a human.
        """
        # This makes sure we raise ObjectNotFound if the exam does not exist
        exam = Exam[exam_id]

        if submission_id is not None:
            s = Submission.get(exam=exam, copy_number=submission_id)
            if not s:
                raise orm.core.ObjectNotFound(Submission)
            return {
                'id': s.copy_number,
                'studentID':  s.student.id if s.student else None,
                'validated': s.signature_validated,
            }

        return [
            {
                'id': s.copy_number,
                'studentID': s.student.id if s.student else None,
                'validated': s.signature_validated,
            }
            for s in Submission.select(lambda s: s.exam == exam)
                               .order_by(Submission.copy_number)
        ]

    put_parser = reqparse.RequestParser()
    put_parser.add_argument('studentID', type=int, required=True)

    @orm.db_session
    def put(self, exam_id, submission_id=None):
        """Assign a student to the given submission.

        Expects a json payload in the format::

            {"studentID": 1234567}


        Parameters
        ----------
        exam_id : int
        submission_id : int
            The copy number of the submission. This uniquely identifies
            the submission *within a given exam*.

        """
        # have to allow 'submission_id' to be optional in the signature
        # because otherwise we just 500 if it's not provided.
        if submission_id is None:
            msg = "Submission ID must be provided when assigning student"
            return dict(status=400, message=msg), 400

        args = self.put_parser.parse_args()

        exam = Exam[exam_id]
        submission = Submission.get(exam=exam, copy_number=submission_id)
        if not submission:
            raise orm.core.ObjectNotFound(Submission)

        student = Student.get(id=args.studentID)
        if not student:
            msg = f'Student {args.studentID} does not exist'
            return dict(status=404, message=msg), 404

        submission.student = student
        submission.signature_validated = True
        return  {
                'id': submission.copy_number,
                'studentID': submission.student.id,
                'validated': ssubmission.signature_validated,
            }
