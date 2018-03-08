from flask_restful import Resource
from pony import orm

from ..models import Exam, Submission

class Submissions(Resource):
    """Getting a list of submissions, and assigning students to them."""

    @orm.db_session
    def get(self, exam_id, copy_number=None):
        """get submissions for the given exam, ordered by copy number.

        Parameters
        ----------
        exam_id : int

        Returns
        -------
        If 'copy_number' not provided provides a single instance of
        (otherwise a list of):
            copy_number: int
            student_id: int or null
                Student that completed this submission, null if not assigned.
            validated: bool
                True if the assigned student has been validated by a human.
        """
        # This makes sure we raise ObjectNotFound if the exam does not exist
        exam = Exam[exam_id]

        if copy_number is not None:
            s = Submission.get(exam=exam, copy_number=copy_number)
            if not s:
                raise orm.core.ObjectNotFound(Submission)
            return {
                'copy_number': s.copy_number,
                'student_id':  s.student.id if s.student else None,
                'validated': s.signature_validated,
            }

        return [
            {
                'copy_number': s.copy_number,
                'student': s.student.id if s.student else None,
                'validated': s.signature_validated,
            }
            for s in Submission.select(lambda s: s.exam == exam)
                               .order_by(Submission.copy_number)
        ]
