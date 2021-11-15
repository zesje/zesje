""" REST api for solutions """

from datetime import datetime

from flask_restful import Resource, reqparse
from flask_restful.inputs import boolean
from flask_login import current_user

from ..database import db, Exam, Submission, Problem, Solution, FeedbackOption


def has_valid_feedback(feedbacks):
    """checks whether a list of FOs is valid according to the exclusivity of their corresponding parets."""
    for fb in feedbacks:
        # not very optimal as it might repeat the search of children multiple times for the same parent
        if fb.parent.mut_excl_children and len([child for child in fb.parent.children if child in feedbacks]) > 1:
            return False
    return True


def remove_feedback_from_solution(fb, solution):
    """Removes a FO from a solution and all its selectec children"""
    solution.feedback.remove(fb)
    for descendant in fb.all_descendants:
        if descendant in solution.feedback:
            solution.feedback.remove(descendant)


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

        return {
            'feedback': [fb.id for fb in solution.feedback],
            'gradedBy': {
                'id': solution.graded_by.id,
                'name': solution.graded_by.name
            } if solution.graded_by else None,
            'gradedAt': solution.graded_at.isoformat() if solution.graded_at else None,
            'remarks': solution.remarks
        }

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
                # go up in the tree checking until we arrive at the top
                if parent.mut_excl_children:
                    # FOs are exclusive -> find other selected children with the same parent as the current `fb_child`
                    # but exclude the current fb (if it is already selected, we do not have to remove)
                    other_checked_children = [
                        child
                        for child in parent.children
                        if child in solution.feedback and child.id != fb_child.id
                    ]
                    if len(other_checked_children) > 0:  # if any, uncheck it
                        # return dict(status=404, message='Another option is already checked.'), 404
                        for other in other_checked_children:  # theoretically, there should be only one...
                            remove_feedback_from_solution(other, solution)
                if fb_child not in solution.feedback:  # and check the new one
                    solution.feedback.append(fb_child)

                # remember the current parent as it will be the child to add in the next iteration
                fb_child = parent

            state = True

        graded = len(solution.feedback)

        if graded and has_valid_feedback(solution.feedback):  # do not approve invalid feedback
            solution.graded_at = datetime.now()
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
            solution.graded_at = datetime.now()
            solution.graded_by = current_user
        else:
            solution.graded_at = None
            solution.graded_by = None

        db.session.commit()

        return {'state': args.approve}
