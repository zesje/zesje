""" REST api for solutions """

from datetime import datetime

from flask_restful import Resource, reqparse

from pony import orm

from ..database import Exam, Submission, Problem, Solution, FeedbackOption


class Solutions(Resource):
    """ Solution provided on a specific problem and exam """

    @orm.db_session
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

        problem = Problem[problem_id]
        exam = Exam[exam_id]

        sub = Submission.get(exam=exam, copy_number=submission_id)
        if not sub:
            raise orm.core.ObjectNotFound(Submission)

        solution = Solution.get(submission=sub, problem=problem)
        if not solution:
            raise orm.core.ObjectNotFound(Solution)

        return {
            'feedback': [fb.id for fb in solution.feedback],
            'gradedBy': solution.graded_by,
            'gradedAt': solution.graded_at.isoformat() if solution.graded_at else None,
            'remarks': solution.remarks
        }

    post_parser = reqparse.RequestParser()
    post_parser.add_argument('remark', type=str, required=True)

    @orm.db_session
    def post(self, exam_id, submission_id, problem_id):
        """Toggles an existing feedback option

        Parameters
        ----------
            remark: string

        Returns
        -------
            true (if succesfull)
        """

        problem = Problem[problem_id]
        exam = Exam[exam_id]

        sub = Submission.get(exam=exam, copy_number=submission_id)
        if not sub:
            raise orm.core.ObjectNotFound(Submission)

        solution = Solution.get(submission=sub, problem=problem)
        if not solution:
            raise orm.core.ObjectNotFound(Solution)

        args = self.post_parser.parse_args()

        solution.graded_at = datetime.now()

        solution.remarks = args.remark

        return True

    put_parser = reqparse.RequestParser()
    put_parser.add_argument('id', type=int, required=True)

    @orm.db_session
    def put(self, exam_id, submission_id, problem_id):
        """Toggles an existing feedback option

        Parameters
        ----------
            id: int

        Returns
        -------
            state: boolean
        """

        problem = Problem[problem_id]
        exam = Exam[exam_id]

        sub = Submission.get(exam=exam, copy_number=submission_id)
        if not sub:
            raise orm.core.ObjectNotFound(Submission)

        solution = Solution.get(submission=sub, problem=problem)
        if not solution:
            raise orm.core.ObjectNotFound(Solution)

        args = self.put_parser.parse_args()

        fb = FeedbackOption.get(id=args.id)
        if not fb:
            raise orm.core.ObjectNotFound(FeedbackOption)

        solution.graded_at = datetime.now()

        if fb in solution.feedback:
            solution.feedback.remove(fb)
            return {'state': False}
        else:
            solution.feedback.add(fb)
            return {'state': True}
