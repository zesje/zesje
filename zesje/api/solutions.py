""" REST api for solutions """

from datetime import datetime

from flask_restful import Resource, reqparse
from flask_restful.inputs import boolean
from flask_login import current_user

from ..database import db, Exam, Submission, Problem, Solution, FeedbackOption


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
            solution.feedback.remove(fb)
            for descendant in fb.all_descendants:
                if descendant in solution.feedback:
                    solution.feedback.remove(descendant)
            state = False
        else:
            solution.feedback.append(fb)
            for ancestor in fb.all_ancestors:
                if ancestor not in solution.feedback:
                    solution.feedback.append(ancestor)
            state = True

        graded = len(solution.feedback)

        if graded:
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

        if graded:
            if args.approve:
                solution.graded_at = datetime.now()
                solution.graded_by = current_user
            else:
                solution.graded_at = None
                solution.graded_by = None
            db.session.commit()
        else:
            return dict(status=409, message='At least one feedback option must be selected.'), 409

        return {'state': args.approve}
