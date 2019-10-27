from flask_restful import Resource, reqparse
from sqlalchemy.orm import selectinload

from ..database import db, Exam, Submission, Student, Page
from ..pregrader import ungrade_multiple_sub


def sub_to_data(sub):
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
                'remark': sol.remarks if sol.remarks else ""
            } for sol in sub.solutions  # Sorted by sol.problem_id
        ]
    }

class Submissions(Resource):
    """Getting a list of submissions, and assigning students to them."""

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
        """
        if submission_id is not None:
            sub = Submission.query.filter(Submission.exam_id == exam_id,
                                          Submission.copy_number == submission_id).one_or_none()
            if sub is None:
                return dict(status=404, message='Submission does not exist.'), 404

            return sub_to_data(sub)

        return [
            sub_to_data(sub) for sub
            in (Submission.query
                .filter(Submission.exam_id == exam_id)
                .order_by(Submission.copy_number).all())
        ]

    put_parser = reqparse.RequestParser()
    put_parser.add_argument('studentID', type=int, required=True)

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

        exam = Exam.query.get(exam_id)
        if exam is None:
            return dict(status=404, message='Exam does not exist.'), 404

        sub = Submission.query.filter(Submission.exam_id == exam.id,
                                      Submission.copy_number == submission_id).one_or_none()
        if sub is None:
            return dict(status=404, message='Submission does not exist.'), 404

        student = Student.query.get(args.studentID)
        if student is None:
            msg = f'Student {args.studentID} does not exist'
            return dict(status=404, message=msg), 404

        old_student_id = sub.student.id if sub.student else -1

        sub.student = student
        sub.signature_validated = True

        # Mark all solutions of this student as ungraded if a new student is assigned
        if args.studentID != old_student_id:
            ungrade_multiple_sub(args.studentID, sub.exam_id, commit=False)

        db.session.commit()
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
                    } for sol in sub.solutions  # Sorted by sol.problem_id
                    ]
        }


class MissingPages(Resource):

    def get(self, exam_id, submission_id=None):

        """get missing pages for each submissino in a given exam, or for a specific
        submission if submission_id is specified.

        Parameters
        ----------
        exam_id : int
        submission_id : int, optional
            The copy number of the submission. This uniquely identifies
            the submission *within a given exam*.

        Returns
        -------
        If 'submission_id' provided provides a single instance of
        (otherwise a list of):
            copyID: int
            missing_pages: list of ints
        """

        # Load exam using the following most efficient strategy
        exam = Exam.query.options(selectinload(Exam.submissions).
                                  subqueryload(Submission.solutions)).get(exam_id)
        if exam is None:
            return dict(status=404, message='Exam does not exist.'), 404

        # Some pages might not have a problem widget (e.g. title page) and some
        # pages might not have been uploaded yet.
        all_pages = set(prob.widget.page for prob in exam.problems)\
            .union(page.number for page in Page.query.join(Submission, isouter=True)
                                                     .join(Exam, isouter=True)
                                                     .filter(Exam.id == exam.id)
                                                     .distinct(Page.number).all())

        if submission_id is not None:
            sub = Submission.query.filter(Submission.exam_id == exam_id,
                                          Submission.copy_number == submission_id).one_or_none()
            if sub is None:
                return dict(status=404, message='Submission does not exist.'), 404
            return {
                'id': sub.copy_number,
                'missing_pages': sorted(all_pages - set(page.number for page in sub.pages)),
            }

        return [
            {
                'id': sub.copy_number,
                'missing_pages': sorted(all_pages - set(page.number for page in sub.pages)),
            } for sub
            in (Submission.query
                .filter(Submission.exam_id == exam_id)
                .order_by(Submission.copy_number).all())
        ]
