from hashlib import md5
from sqlalchemy.sql import operators
from flask_restful import Resource, reqparse
from flask_restful.inputs import boolean
from flask_login import current_user

from .solutions import solution_to_data
from ..database import Exam, Submission, Problem


def sub_to_data(sub, meta=None):
    """Transform a submission into a data structure frontend expects."""
    return {
        'meta': meta,
        'id': sub.id,
        'student': {
            'id': sub.student.id,
            'firstName': sub.student.first_name,
            'lastName': sub.student.last_name,
            'email': sub.student.email
        } if sub.student else None,
        'validated': sub.validated,
        'problems': [
            solution_to_data(sol) for sol in sub.solutions  # Sorted by sol.problem_id
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


def all_filters(sol, required_feedback, excluded_feedback, graded_by, ungraded):
    """
    Returns whether a submission meets all requirements.

    Parameters
    ----------

    sol: Solution
        the solution to check if it meets all the requirements.
    required_feedback: Set[int]
        the feedback_id's which the submission should have.
    excluded_feedback: Set[int]
        the feedback_id's which the submission should not have.
    graded_by: int
        the id of the grader that should have graded the exam, optional
    ungraded: bool
        value whether the solution should be ungraded or you do not care.

    Retuns
    ----------
    If this current submission matches all the filters.
    """
    return (has_all_required_feedback(sol, required_feedback, excluded_feedback) and
            (graded_by is None or (sol.graded_by is not None and sol.graded_by.id == graded_by)) and
            (not ungraded or sol.graded_by is None))


def find_number_of_matches(problem, ungraded, required_feedback, excluded_feedback, graded_by):
    """
    Finds the number of solutions that match all the filtering criteria.

    Parameters
    ----------
    problem : Problem
        current problem.
    ungraded: bool
        value whether the solution should be ungraded or you do not care.
    required_feedback : List[int]
        the feedback_id's which the matched submissions should have.
    excluded_feedback : List[int]
        the feedback_id's which the macthed submissions should not have.
    graded_by : int
        the id of the grader that should have graded the matched submissions, optional.

    Returns
    --------
    The number of submissions that match all the filtering criteria.
    """
    return sum(
        all_filters(sol, set(required_feedback), set(excluded_feedback), graded_by, ungraded)
        for sol in problem.solutions
    )


def _find_submission(old_submission, problem, shuffle_seed, direction, ungraded,
                     required_feedback, excluded_feedback, graded_by):
    """
    Finds a submission based on the parameters of the function.
    Finds all solutions for the problem, and shuffles them based on the shuffle_seed.
    Then finds the first (ungraded) submission, either in 'next' or 'prev' direction or 'first' or 'last'.
    If no such submission exists, returns the old submission.

    Parameters
    ----------
    old_submission : Submission
        the submission to base next or prev on.
    problem : Problem
        current problem.
    shuffle_seed : int
        the seed to shuffle the submissions on.
    direction : string
        either 'next', 'prev', 'first' or 'last'
    ungraded : bool
        value indicating whether the found submission should be ungraded.
    required_feedback : List[int]
        the feedback_id's which the found submission should have
    excluded_feedback : List[int]
        the feedback_id's which the found submission should not have
    graded_by : int
        the id of the grader that should have graded that submission, optional

    Returns
    -------
    A new submission, or the old one if no submission matching the criteria is found.
    """
    def key(sub):
        return md5(b'%i %i' % (sub.id, shuffle_seed)).digest()

    old_key = key(old_submission)
    next_, follows, precedes = {
      'next': (min, operators.gt, operators.lt),
      'prev': (max, operators.lt, operators.gt),
      'first': (min, operators.lt, operators.gt),
      'last': (max, operators.gt, operators.lt)
    }[direction]
    required_feedback = set(required_feedback)
    excluded_feedback = set(excluded_feedback)

    count_follows = 0
    count_precedes = 0
    match_current = False
    sub = None
    for item in (
        sol.submission for sol in problem.solutions
        if all_filters(sol, required_feedback, excluded_feedback, graded_by, ungraded)
    ):
        if follows(key(item), old_key):
            count_follows += 1
            if sub:
                sub = next_(sub, item, key=key)
            else:
                sub = item
        elif precedes(key(item), old_key):
            count_precedes += 1
        else:
            match_current = True

    return sub if sub else old_submission, count_follows, count_precedes, match_current


class Submissions(Resource):
    """Getting a list of submissions"""

    get_parser = reqparse.RequestParser()
    get_parser.add_argument('problem_id', type=int, required=False)
    get_parser.add_argument('ungraded', type=boolean, required=False, default=False)
    get_parser.add_argument('direction', type=str, required=False, choices=["next", "prev", "first", "last"])
    get_parser.add_argument('required_feedback', type=int, required=False, action='append')
    get_parser.add_argument('excluded_feedback', type=int, required=False, action='append')
    get_parser.add_argument('graded_by', type=int, required=False)

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
        Either a single dictionary with the data of the requested submission, or
        a list of such dictionaries corresponding to all submissions in the exam.

        See `sub_to_data` for the dictionary format.
        """
        args = self.get_parser.parse_args()
        if (exam := Exam.query.get(exam_id)) is None:
            return dict(status=404, message='Exam does not exist.'), 404

        if submission_id is None:
            return [sub_to_data(sub) for sub in exam.submissions]

        if (sub := Submission.query.get(submission_id)) is None:
            return dict(status=404, message='Submission does not exist.'), 404

        if sub.exam != exam:
            return dict(status=400, message='Submission does not belong to this exam.'), 400

        problem = None
        n_graded = None
        if args.problem_id:
            if (problem := Problem.query.get(args.problem_id)) is None:
                return dict(status=404, message='Problem does not exist.'), 404
            n_graded = sum(1 for sol in problem.solutions if sol.graded_by is not None)

        new_sub, no_of_subs_follow, no_of_subs_precede, match_current = _find_submission(
            sub, problem, current_user.id, args.direction or 'next', args.ungraded,
            args.required_feedback or [], args.excluded_feedback or [], args.graded_by
        )
        if not args.direction:
            new_sub = sub

        matched = no_of_subs_follow + no_of_subs_precede + match_current
        if args.direction is None:
            no_next_sub = no_of_subs_follow == 0
            no_prev_sub = no_of_subs_precede == 0
        elif args.direction in ('next', 'prev'):
            no_next_sub = no_of_subs_follow <= 1
            no_prev_sub = (no_of_subs_precede + match_current) == 0
        elif args.direction in ('last', 'first'):
            no_next_sub = True
            no_prev_sub = matched <= 1

        # If direction is backwards the availability of subs should be inverted
        if args.direction in ('prev', 'first'):
            no_next_sub, no_prev_sub = no_prev_sub, no_next_sub

        meta = {
            'filter_matches': matched,
            'n_graded': n_graded,
            'no_next_sub': no_next_sub,
            'no_prev_sub': no_prev_sub,
        }

        return sub_to_data(new_sub, meta)
