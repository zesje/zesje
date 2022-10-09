""" REST api for solutions """

from datetime import datetime, timezone

from flask_restful import Resource, reqparse
from flask_restful.inputs import boolean
from flask_login import current_user

from ..database import db, Exam, Submission, Problem, Solution, FeedbackOption


def has_valid_feedback(feedbacks):
    """checks whether a list of FOs is valid according to the exclusivity of their corresponding parets."""
    for fb in feedbacks:
        if fb.parent.mut_excl_children and any(True for child in fb.siblings if child in feedbacks):
            return False
    return True


def remove_feedback_from_solution(fb, solution):
    """Removes a FO from a solution and all its selectec children"""
    solution.feedback.remove(fb)
    for descendant in fb.all_descendants:
        if descendant in solution.feedback:
            solution.feedback.remove(descendant)


def solution_to_data(solution):
    return {
        'problemId': solution.problem_id,
        'feedback': [fb.id for fb in solution.feedback],
        'valid': has_valid_feedback(solution.feedback),
        'gradedBy': {
            'id': solution.graded_by.id,
            'name': solution.graded_by.name,
            'oauth_id': solution.graded_by.oauth_id
        } if solution.graded_by else None,
        'gradedAt': int(solution.graded_at.timestamp() * 1000) if solution.graded_at else None,
        'remark': solution.remarks or ''
    }


class Solutions(Resource):
    """ Solution provided on a specific problem and exam """

    def get(self, exam_id, submission_id, problem_id):
        """get solution to problem

        Returns
        -------
            feedback: list of int (IDs of FeedbackOption)
            gradedBy: grader
            gradedAt: datetime
            imagePath: string (url)
            remarks: string
        """

        if (problem := Problem.query.get(problem_id)) is None:
            return dict(status=404, message='Problem does not exist.'), 404

        if Exam.query.get(exam_id) is None:
            return dict(status=404, message='Exam does not exist.'), 404

        if (sub := Submission.query.get(submission_id)) is None:
            return dict(status=404, message='Submission does not exist.'), 404

        if sub.exam_id != exam_id:
            return dict(status=400, message='Submission does not belong to this exam.'), 400

        solution = Solution.query.filter(Solution.submission_id == sub.id,
                                         Solution.problem_id == problem.id).one_or_none()
        if solution is None:
            return dict(status=404, message='Solution does not exist.'), 404

        return solution_to_data(solution)

    post_parser = reqparse.RequestParser()
    post_parser.add_argument('remark', type=str, required=True)

    def post(self, exam_id, submission_id, problem_id):
        """Change the remark of a solution

        Parameters
        ----------
            remark: string

        Returns
        -------
            true (if succesfull)
        """

        args = self.post_parser.parse_args()

        if (problem := Problem.query.get(problem_id)) is None:
            return dict(status=404, message='Problem does not exist.'), 404

        if Exam.query.get(exam_id) is None:
            return dict(status=404, message='Exam does not exist.'), 404

        if (sub := Submission.query.get(submission_id)) is None:
            return dict(status=404, message='Submission does not exist.'), 404

        if sub.exam_id != exam_id:
            return dict(status=400, message='Submission does not belong to this exam.'), 400

        solution = Solution.query.filter(Solution.submission_id == sub.id,
                                         Solution.problem_id == problem.id).one_or_none()
        if solution is None:
            return dict(status=404, message='Solution does not exist.'), 404

        solution.remarks = args.remark

        db.session.commit()
        return True

    put_parser = reqparse.RequestParser()
    put_parser.add_argument('id', type=int, required=True)

    def put(self, exam_id, submission_id, problem_id):
        """Toggles an existing feedback option

        Parameters
        ----------
            id: int

        Returns
        -------
            state: boolean
        """
        args = self.put_parser.parse_args()
        if (sub := Submission.query.get(submission_id)) is None:
            return dict(status=404, message='Submission does not exist.'), 404

        if sub.exam_id != exam_id:
            return dict(status=400, message='Submission does not belong to this exam.'), 400

        solution = Solution.query.filter(Solution.submission_id == submission_id,
                                         Solution.problem_id == problem_id).one_or_none()
        if solution is None:
            return dict(status=404, message='Solution does not exist.'), 404

        if (fb := FeedbackOption.query.get(args.id)) is None:
            return dict(status=404, message='Feedback Option does not exist.'), 404

        if fb in solution.feedback:
            remove_feedback_from_solution(fb, solution)
            state = False
        else:
            fb_child = fb
            for parent in fb.all_ancestors:
                if parent.mut_excl_children:
                    # Should be exclusive, so we uncheck all siblings
                    for sibling in fb_child.siblings:
                        if sibling in solution.feedback:
                            remove_feedback_from_solution(sibling, solution)

                if fb_child not in solution.feedback:
                    # check the current option
                    solution.feedback.append(fb_child)

                # continue up in the tree
                fb_child = parent

            state = True

        graded = len(solution.feedback)

        if graded and has_valid_feedback(solution.feedback):  # do not approve invalid feedback
            solution.graded_at = datetime.now(timezone.utc)
            solution.graded_by = current_user
        else:
            solution.graded_at = None
            solution.graded_by = None

        db.session.commit()

        return {'state': state}


class Approve(Resource):
    """Mark a solution as graded."""
    put_parser = reqparse.RequestParser()
    put_parser.add_argument('approve', type=boolean, required=True)

    def put(self, exam_id, submission_id, problem_id):
        """Approve a solution or set it aside for later grading.

        If the grader id is provided, the solution is marked as being graded by that grader,
        otherwise it is marked as ungraded. This refuses to mark as graded if no feedback
        is assigned.

        Returns
        -------
            state: boolean
        """
        args = self.put_parser.parse_args()

        if (sub := Submission.query.get(submission_id)) is None:
            return dict(status=404, message='Submission does not exist.'), 404

        if sub.exam_id != exam_id:
            return dict(status=400, message='Submission does not belong to this exam.'), 400

        solution = Solution.query.filter(Solution.submission_id == sub.id,
                                         Solution.problem_id == problem_id).one_or_none()
        if solution is None:
            return dict(status=404, message='Solution does not exist.'), 404

        graded = len(solution.feedback)

        if not graded:
            return dict(status=409, message='At least one feedback option must be selected.'), 409

        if not has_valid_feedback(solution.feedback):
            return dict(status=409, message='Multiple exclusive option are selected for the same parent.'), 409

        if args.approve:
            solution.graded_at = datetime.now(timezone.utc)
            solution.graded_by = current_user
        else:
            solution.graded_at = None
            solution.graded_by = None

        db.session.commit()

        return {'state': args.approve}
