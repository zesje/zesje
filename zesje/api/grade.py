from flask_restful import Resource, reqparse
from flask_restful.inputs import boolean

from zesje.api.submissions import sub_to_data
from zesje.database import Exam, Submission


def _shuffle(submissions, grader_id):
    return sorted(submissions, key=lambda s: hash((str(s.id), grader_id)))


def find_submission(exam_id, submission_id, problem_id, args):
    """
    Finds a submission.
    First finds the Exam and Submission by exam_id, submission_id, and then shuffles exam.submissions
    uniquely for each graderID.
    Then finds the next/previous graded/ungraded submission, based on the the request arguments.
    :param exam_id: exam_id to find submission for
    :param submission_id: the old submission copy number, to base what is 'next' on.
    :param problem_id: the current problem_id.
    :param args: object containing grader_id, ungraded, and direction.
    :return: the next (un)graded submission in the specified direction, or the same if none exists.
    """
    exam = Exam.query.get(exam_id)
    if exam is None:
        return dict(status=404, message='Exam does not exist.'), 404

    old_submission = Submission.query.filter(Submission.exam_id == exam.id,
                                             Submission.copy_number == submission_id).one_or_none()
    if old_submission is None:
        return dict(status=404, message='Submission does not exist.'), 404

    shuffled_submissions = _shuffle(exam.submissions, args.grader_id)
    old_submission_index = shuffled_submissions.index(old_submission)

    if not args.ungraded:
        offset = 1 if args.direction == 'next' else - 1
        new_index = old_submission_index + offset
        if 0 <= new_index < len(shuffled_submissions):
            return sub_to_data(shuffled_submissions[old_submission_index + offset])
        return sub_to_data(old_submission)

    # If direction is next, search submissions from the one after the old, up to the end of the list.
    # If direction is previous search from the start to the old, in reverse order.
    submissions_to_search = shuffled_submissions[old_submission_index + 1:] if args.direction == 'next' \
        else shuffled_submissions[old_submission_index - 1::-1]

    if len(submissions_to_search) == 0:
        return sub_to_data(old_submission)

    # Get the next submission for which the solution to our problem was not graded yet
    submission = next((submission for submission in submissions_to_search if
                      any(sol.problem_id == problem_id and not sol.graded_by for sol in submission.solutions)),
                      old_submission)  # Returns the old submission in case no suitable submission was found
    return sub_to_data(submission)


class Navigation(Resource):
    """Api endpoint for navigation in the grade page"""

    get_parser = reqparse.RequestParser()
    get_parser.add_argument('ungraded', type=boolean, required=True)
    get_parser.add_argument('grader_id', type=int, required=True)
    get_parser.add_argument('direction', type=str, required=True, choices=['prev', 'next'])

    def get(self, exam_id, submission_id, problem_id):
        args = self.get_parser.parse_args()
        return find_submission(exam_id, submission_id, problem_id, args)


class Metadata(Resource):
    """Api endpoint for metadata for an exam"""

    def get(self, exam_id):
        """ Serves metadata for an exam.

        :param exam_id: id of exam to get metadata for.
        :return: the exam metadata.
        """
        exam = Exam.query.get(exam_id)
        if exam is None:
            return dict(status=404, message='Exam does not exist.'), 404

        return {
            'exam_id': exam.id,
            'submissions': [
                {
                    'id': sub.copy_number,
                    'student': {
                        'id': sub.student.id,
                        'firstName': sub.student.first_name,
                        'lastName': sub.student.last_name,
                        'email': sub.student.email
                    } if sub.student else None
                } for sub in exam.submissions
            ],
            'problems': [
                {
                    'id': problem.id,
                    'name': problem.name,
                } for problem in exam.problems]

        }
