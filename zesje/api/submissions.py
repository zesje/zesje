from flask_restful import Resource, reqparse
from flask_restful.inputs import boolean

from zesje.api._helpers import _shuffle
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


# Returns true if the solution meets the requirements
def has_all_required_feedback(sol, required_feedback, excluded_feedback):
    has_required = required_feedback is None or \
         all(fb_id in sol.feedback for fb_id in required_feedback)
    if has_required:
        doesnt_have_excluded = excluded_feedback is None or not \
            any(fb_id in sol.feedback for fb_id in excluded_feedback)
        return doesnt_have_excluded
    else:
        return False


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
    Returns
    -------
    A new submission, or the old one if no submission matching the criteria is found.

    """

    if (problem := Problem.query.get(problem_id)) is None:
        return dict(status=404, message='Problem does not exist.'), 404

    filtered_solutions = [
            sol for sol in problem.solutions if
            sol.submission_id == old_submission.id or
            has_all_required_feedback(sol, required_feedback, excluded_feedback)
        ]
    # Make shuffled_solutions smaller by only including solutions fitting criteria or the solution currently open.
    shuffled_solutions = _shuffle(filtered_solutions, shuffle_seed, key_extractor=lambda s: s.submission_id)

    # This new list is then used to find the next submission in the same way as before.
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
