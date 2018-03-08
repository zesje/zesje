from flask_restful import Resource
from pony import orm

from ..models import Exam, Submission

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
