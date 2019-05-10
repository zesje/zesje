""" REST api for solutions """

from datetime import datetime

from flask_restful import Resource, reqparse

from pony import orm

from ..database import Exam, Submission, Problem, Solution, FeedbackOption, Grader


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

    @orm.db_session
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

        problem = Problem[problem_id]
        exam = Exam[exam_id]

        sub = Submission.get(exam=exam, copy_number=submission_id)
        if not sub:
            raise orm.core.ObjectNotFound(Submission)

        solution = Solution.get(submission=sub, problem=problem)
        if not solution:
            raise orm.core.ObjectNotFound(Solution)

        solution.remarks = args.remark

        return True

    put_parser = reqparse.RequestParser()
    put_parser.add_argument('id', type=int, required=True)
    put_parser.add_argument('graderID', type=int, required=True)

    @orm.db_session
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

        problem = Problem[problem_id]
        exam = Exam[exam_id]
        grader = Grader[args.graderID]

        sub = Submission.get(exam=exam, copy_number=submission_id)
        if not sub:
            raise orm.core.ObjectNotFound(Submission)

        solution = Solution.get(submission=sub, problem=problem)
        if not solution:
            raise orm.core.ObjectNotFound(Solution)

        fb = FeedbackOption.get(id=args.id)
        if not fb:
            raise orm.core.ObjectNotFound(FeedbackOption)

        if fb in solution.feedback:
            solution.feedback.remove(fb)
            state = False
        else:
            solution.feedback.add(fb)
            state = True

        graded = len(solution.feedback)

        if graded:
            solution.graded_at = datetime.now()
            solution.graded_by = grader
        else:
            solution.graded_at = None
            solution.graded_by = None

        return {'state': state}


class Approve(Resource):    
    """ add just a grader to a specifc problem on an exam """
    put_parser = reqparse.RequestParser()
    put_parser.add_argument('graderID', type=int, required=True)

    @orm.db_session
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

        problem = Problem[problem_id]
        exam = Exam[exam_id]
        grader = Grader[args.graderID]

        sub = Submission.get(exam=exam, copy_number=submission_id)
        if not sub:
            raise orm.core.ObjectNotFound(Submission)

        solution = Solution.get(submission=sub, problem=problem)
        if not solution:
            raise orm.core.ObjectNotFound(Solution)

        graded = len(solution.feedback)

        if graded:
            solution.graded_at = datetime.now()
            solution.graded_by = grader

        return {'state': graded}
