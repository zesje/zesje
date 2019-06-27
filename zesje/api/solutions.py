""" REST api for solutions """

from datetime import datetime

from flask_restful import Resource, reqparse

from ..database import db, Exam, Submission, Problem, Solution, FeedbackOption, Grader


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

        problem = Problem.query.get(problem_id)
        if problem is None:
            return dict(status=404, message='Problem does not exist.'), 404

        exam = Exam.query.get(exam_id)
        if exam is None:
            return dict(status=404, message='Exam does not exist.'), 404

        sub = Submission.query.filter(Submission.exam_id == exam.id,
                                      Submission.copy_number == submission_id).one_or_none()
        if sub is None:
            return dict(status=404, message=f'Submission does not exist.'), 404

        solution = Solution.query.filter(Solution.submission_id == sub.id,
                                         Solution.problem_id == problem.id).one_or_none()
        if solution is None:
            return dict(status=404, message=f'Solution does not exist.'), 404

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
    post_parser.add_argument('graderID', type=int, required=True)

    def post(self, exam_id, submission_id, problem_id):
        """Change the remark of a solution

        Parameters
        ----------
            remark: string
            graderID: int

        Returns
        -------
            true (if succesfull)
        """

        args = self.post_parser.parse_args()

        problem = Problem.query.get(problem_id)
        if problem is None:
            return dict(status=404, message='Problem does not exist.'), 404

        exam = Exam.query.get(exam_id)
        if exam is None:
            return dict(status=404, message='Exam does not exist.'), 404

        sub = Submission.query.filter(Submission.exam_id == exam.id,
                                      Submission.copy_number == submission_id).one_or_none()
        if sub is None:
            return dict(status=404, message='Submission does not exist.'), 404

        solution = Solution.query.filter(Solution.submission_id == sub.id,
                                         Solution.problem_id == problem.id).one_or_none()
        if solution is None:
            return dict(status=404, message='Solution does not exist.'), 404

        solution.remarks = args.remark

        db.session.commit()
        return True

    put_parser = reqparse.RequestParser()
    put_parser.add_argument('id', type=int, required=True)
    put_parser.add_argument('graderID', type=int, required=True)

    def put(self, exam_id, submission_id, problem_id):
        """Toggles an existing feedback option

        Parameters
        ----------
            id: int
            graderID: int

        Returns
        -------
            state: boolean
        """
        args = self.put_parser.parse_args()

        grader = Grader.query.get(args.graderID)
        if grader is None:
            return dict(status=404, message='Grader does not exist.'), 404

        sub = Submission.query.filter(Submission.exam_id == exam_id,
                                      Submission.copy_number == submission_id).one_or_none()
        if sub is None:
            return dict(status=404, message='Submission does not exist.'), 404

        solution = Solution.query.filter(Solution.submission_id == sub.id,
                                         Solution.problem_id == problem_id).one_or_none()
        if solution is None:
            return dict(status=404, message='Solution does not exist.'), 404

        fb = FeedbackOption.query.get(args.id)
        if fb is None:
            return dict(status=404, message='Feedback Option does not exist.'), 404

        if fb in solution.feedback:
            solution.feedback.remove(fb)
            state = False
        else:
            solution.feedback.append(fb)
            state = True

        graded = len(solution.feedback)

        if graded:
            solution.graded_at = datetime.now()
            solution.graded_by = grader
        else:
            solution.graded_at = None
            solution.graded_by = None

        db.session.commit()

        return {'state': state}


class Approve(Resource):
    """Mark a solution as graded."""
    put_parser = reqparse.RequestParser()
    put_parser.add_argument('graderID', type=int, required=True)

    def put(self, exam_id, submission_id, problem_id):
        """Takes an existing feedback checks if it is valid then gives the current graders id to the solution this is
        usefull for approving pre graded solutions

        Parameters
        ----------
            graderID: int

        Returns
        -------
            state: boolean
        """
        args = self.put_parser.parse_args()

        grader = Grader.query.get(args.graderID)

        sub = Submission.query.filter(Submission.exam_id == exam_id,
                                      Submission.copy_number == submission_id).one_or_none()
        if sub is None:
            return dict(status=404, message='Submission does not exist.'), 404

        solution = Solution.query.filter(Solution.submission_id == sub.id,
                                         Solution.problem_id == problem_id).one_or_none()
        if solution is None:
            return dict(status=404, message='Solution does not exist.'), 404

        graded = len(solution.feedback)

        if graded:
            solution.graded_at = datetime.now()
            solution.graded_by = grader
            db.session.commit()
        else:
            return dict(status=409, message='At least one feedback option must be selected.'), 409

        return {'state': graded}
