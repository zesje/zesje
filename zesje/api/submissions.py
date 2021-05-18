from hashlib import md5
from sqlalchemy.sql import operators
from flask_restful import Resource, reqparse
from flask_restful.inputs import boolean

from ..database import Exam, Submission, Problem


def sub_to_data(sub):
    """Transform a submission into a data structure frontend expects."""
    return {
        'id': sub.id,
        'student': {
            'id': sub.student.id,
            'firstName': sub.student.first_name,
            'lastName': sub.student.last_name,
            'email': sub.student.email
        } if sub.student else None,
        'validated': sub.validated,
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


def has_all_required_feedback(sol, required_feedback, excluded_feedback):
    """
    If solution has all the required feedback and non of the excluded_feedback returns true
    else return false.

    Parameters
    ----------
    sol : Solution
        the solution to be checked
    required_feedback : Set[int]
        the feedback_id's which the found submission should have
    excluded_feedback : Set[int]
        the feedback_id's which the found submission should not have

    Returns
    -------
    A boolean, true if sol meets all requirements false otherwhise.

    """
    feedback_ids = set(fb.id for fb in sol.feedback)
    return (required_feedback <= feedback_ids) and (not excluded_feedback & feedback_ids)


def _find_submission(old_submission, problem_id, shuffle_seed, direction, ungraded,
                     required_feedback, excluded_feedback):
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
    required_feedback : List[int]
        the feedback_id's which the found submission should have
    excluded_feedback : List[int]
        the feedback_id's which the found submission should not have
    Returns
    -------
    A new submission, or the old one if no submission matching the criteria is found.

    """

    if (problem := Problem.query.get(problem_id)) is None:
        return dict(status=404, message='Problem does not exist.'), 404

    def key(sub):
        return md5(b'%i %i' % (sub.id, shuffle_seed)).digest()
    old_key = key(old_submission)
    next_, follows = (min, operators.gt) if direction == 'next' else (max, operators.lt)
    required_feedback = set(required_feedback or [])
    excluded_feedback = set(excluded_feedback or [])
    submission_to_return = next_(
      (
        sol.submission for sol in problem.solutions
        if (
          has_all_required_feedback(sol, required_feedback, excluded_feedback)
          and follows(key(sol.submission), old_key)
          and (not ungraded or sol.graded_by is None)
        )
      ),
      key=key,
      default=old_submission
    )
    return sub_to_data(submission_to_return)


class Submissions(Resource):
    """Getting a list of submissions"""

    get_parser = reqparse.RequestParser()
    get_parser.add_argument('problem_id', type=int, required=False)
    get_parser.add_argument('shuffle_seed', type=int, required=False)
    get_parser.add_argument('ungraded', type=boolean, required=False)
    get_parser.add_argument('direction', type=str, required=False, choices=["next", "prev"])
    get_parser.add_argument('required_feedback', type=int, required=False, action='append')
    get_parser.add_argument('excluded_feedback', type=int, required=False, action='append')

    def get(self, exam_id, submission_id=None):
        """get submissions for the given exam

        if args.direction is specified, returns a submission based on
        the _find_submissions function.

        Parameters
        ----------
        exam_id : int
            The id of the exam for which the submissions must be returned
        submission_id : int, optional
            The id of the submission. This uniquely identifies
            the submission *across all exams*.

        Returns
        -------
        If 'submission_id' not provided provides a single instance of
        (otherwise a list of):
            id: int
            student: Student
                Student that completed this submission, null if not assigned.
            problems: list of problems
        """
        args = self.get_parser.parse_args()
        if (exam := Exam.query.get(exam_id)) is None:
            return dict(status=404, message='Exam does not exist.'), 404

        if submission_id is not None:
            if (sub := Submission.query.get(submission_id)) is None:
                return dict(status=404, message='Submission does not exist.'), 404

            if sub.exam != exam:
                return dict(status=400, message='Submission does not belong to this exam.'), 400

            if args.direction:
                if args.problem_id is None or args.shuffle_seed is None or args.ungraded is None:
                    return dict(status=400, message='One of problem_id, grader_id, ungraded, direction not provided')
                return _find_submission(sub, args.problem_id, args.shuffle_seed, args.direction, args.ungraded,
                                        args.required_feedback, args.excluded_feedback)

            return sub_to_data(sub)

        return [sub_to_data(sub) for sub in exam.submissions]
