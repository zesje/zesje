import os

from flask import current_app
from flask_restful import Resource, reqparse
from flask_restful.inputs import boolean
from pdfrw import PdfReader

from zesje.api._helpers import _shuffle
from ..database import db, Exam, Submission, Student, Problem
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


def _find_submission(old_submission, problem_id, shuffle_seed, direction, ungraded):
    """
    Finds a submission based on the parameters of the function.
    Finds all solutions for the problem, and shuffles them based on the shuffle_seed.
    Then finds the first (ungraded) submission, either in 'next' or 'prev' direction.
    If no such submission exists, returns the old submission.

    Parameters
    ----------
    old_submission : submission
        the submission to base next or prev on.
    problem_id : int
        id of the current problem.
    shuffle_seed : int
        the seed to shuffle the submissions on.
    direction : string
        either 'next' or 'prev'
    ungraded : bool
        value indicating whether the found submission should be ungraded.
    Returns
    -------
    A new submission, or the old one if no submission matching the criteria is found.

    """

    problem = Problem.query.get(problem_id)

    if problem is None:
        return dict(status=404, message='Problem does not exist.'), 404

    shuffled_solutions = _shuffle(problem.solutions, shuffle_seed, key_extractor=lambda s: s.submission_id)
    old_submission_index = next(i for i, s in enumerate(shuffled_solutions) if s.submission_id == old_submission.id)

    if (old_submission_index == 0 and direction == 'prev') or \
            (old_submission_index == len(shuffled_solutions) - 1 and direction == 'next'):
        return sub_to_data(old_submission)

    if not ungraded:
        offset = 1 if direction == 'next' else -1
        return sub_to_data(shuffled_solutions[old_submission_index + offset].submission)

    # If direction is next, search submissions from the one after the old, up to the end of the list.
    # If direction is previous search from the start to the old, in reverse order.
    solutions_to_search = shuffled_solutions[old_submission_index + 1:] if direction == 'next' \
        else shuffled_solutions[old_submission_index - 1::-1]

    if len(solutions_to_search) == 0:
        return sub_to_data(old_submission)

    # Get the next submission for which the solution to our problem was not graded yet
    submission = next((solution.submission for solution in solutions_to_search if
                       solution.graded_by is None),
                      old_submission)  # Returns the old submission in case no suitable submission was found
    return sub_to_data(submission)


class Submissions(Resource):
    """Getting a list of submissions, and assigning students to them."""

    get_parser = reqparse.RequestParser()
    get_parser.add_argument('problem_id', type=int, required=False)
    get_parser.add_argument('shuffle_seed', type=int, required=False)
    get_parser.add_argument('ungraded', type=boolean, required=False)
    get_parser.add_argument('direction', type=str, required=False, choices=["next", "prev"])

    def get(self, exam_id, submission_id=None):
        """get submissions for the given exam, ordered by copy number.

        if args.direction is specified, returns a submission based on
        the _find_submissions function.

        Parameters
        ----------
        exam_id : int
            The id of the exam for which the missing pages must be computed.
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
        args = self.get_parser.parse_args()
        exam = Exam.query.get(exam_id)
        if exam is None:
            return dict(status=404, message='Exam does not exist.'), 404

        if submission_id is not None:
            sub = Submission.query.filter(Submission.exam_id == exam_id,
                                          Submission.copy_number == submission_id).one_or_none()
            if sub is None:
                return dict(status=404, message='Submission does not exist.'), 404

            if args.direction:
                if args.problem_id is None or args.shuffle_seed is None or args.ungraded is None:
                    return dict(status=400, message='One of problem_id, grader_id, ungraded, direction not provided')
                return _find_submission(sub, args.problem_id, args.shuffle_seed, args.direction, args.ungraded)

            return sub_to_data(sub)

        return [sub_to_data(sub) for sub in exam.submissions]

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
        return dict(status=200, message=f'Student {student.id} matched to submission {sub.copy_number}'), 200


class MissingPages(Resource):

    def get(self, exam_id):
        """
        Compute which submissions are missing which pages.

        Parameters
        ----------
        exam_id : int
            The id of the exam for which the missing pages must be computed.

        Returns
        -------
        Provides a list of:
            copyID: int
            missing_pages: list of ints
        """

        exam = Exam.query.get(exam_id)

        if exam is None:
            return dict(status=404, message='Exam does not exist.'), 404

        all_pages = set(range(len(
            PdfReader(os.path.join(current_app.config['DATA_DIRECTORY'], f'{exam_id}_data/exam.pdf')).pages)
        ))
        return [
            {
                'id': sub.copy_number,
                'missing_pages': sorted(all_pages - set(page.number for page in sub.pages)),
            } for sub in exam.submissions
        ]
