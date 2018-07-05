from flask_restful import Resource, reqparse

from pony import orm

from ..database import Exam, Submission, Student


def sub_to_data(sub, all_pages):
    """Transform a submission into a data structure frontend expects."""
    return {
        'id': sub.copy_number,
        'student': {
            'id': sub.student.id,
            'firstName': sub.student.first_name,
            'lastName': sub.student.last_name,
            'email': sub.student.email
        } if sub.student else None,
        'validated': sub.signature_validated,
        'problems': [
            {
                'id': sol.problem.id,
                'graded_by': {
                    'id': sol.graded_by.id,
                    'name': sol.graded_by.name
                } if sol.graded_by else None,
                'graded_at': sol.graded_at.isoformat() if sol.graded_at else None,
                'feedback': [
                    fb.id for fb in sol.feedback
                ],
                'remark': sol.remarks
            } for sol in sub.solutions.order_by(lambda s: s.problem.id)
        ],
        'missing_pages': sorted(all_pages - set(sub.pages.number)),
    }


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
            problems: list of problems
            missing_pages: list of int
                pages that are missing from submission
        """
        # This makes sure we raise ObjectNotFound if the exam does not exist
        exam = Exam[exam_id]

        # Some pages might not have a problem widget (e.g. title page) and some
        # pages might not have been uploaded yet.
        all_pages = set(exam.problems.widget.page).union(exam.submissions.pages.number)

        if submission_id is not None:
            sub = Submission.get(exam=exam, copy_number=submission_id)
            if not sub:
                raise orm.core.ObjectNotFound(Submission)

            return sub_to_data(sub, all_pages)

        return [
            sub_to_data(sub, all_pages) for sub
            in (Submission
                .select(lambda s: s.exam == exam)
                .order_by(lambda s: s.copy_number))
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
        sub = Submission.get(exam=exam, copy_number=submission_id)
        if not sub:
            raise orm.core.ObjectNotFound(Submission)

        student = Student.get(id=args.studentID)
        if not student:
            msg = f'Student {args.studentID} does not exist'
            return dict(status=404, message=msg), 404

        sub.student = student
        sub.signature_validated = True
        return {
            'id': sub.copy_number,
            'student':
                {
                    'id': sub.student.id,
                    'firstName': sub.student.first_name,
                    'lastName': sub.student.last_name,
                    'email': sub.student.email
                } if sub.student else None,
            'validated': sub.signature_validated,
            'problems': [
                    {
                        'id': sol.problem.id,
                        'graded_by': {
                            'id': sol.graded_by.id,
                            'name': sol.graded_by.name
                        } if sol.graded_by else None,
                        'graded_at': sol.graded_at.isoformat() if sol.graded_at else None,
                        'feedback': [
                            fb.id for fb in sol.feedback
                        ],
                        'remark': sol.remarks
                    } for sol in sub.solutions.order_by(lambda s: s.problem.id)
                    ]
        }
