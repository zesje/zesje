""" REST api for problems """

from flask_restful import Resource, reqparse
from flask_restful.inputs import boolean
from sqlalchemy import func
import numpy as np

from ..database import db, Problem, FeedbackOption, Solution, solution_feedback


def feedback_to_data(feedback, full_children=True):
    return {
        'id': feedback.id,
        'name': feedback.text,
        'description': feedback.description,
        'score': feedback.score,
        'parent': feedback.parent_id,
        'used': len(feedback.solutions),
        'children': [feedback_to_data(child) if full_children else child.id for child in feedback.children],
        'exclusive': feedback.mut_excl_children
    }


class Feedback(Resource):
    """ List of feedback options of a problem """

    def get(self, problem_id):
        """get list of feedback connected to a specific problem

        Returns
        -------
        list of:
            id: int
            name: str
            description: str
            score: int
            parent: int
            used: int
            children: List(int)
                list of children ids

        """

        if (problem := Problem.query.get(problem_id)) is None:
            return dict(status=422, message=f"Problem with id #{problem_id} does not exist"), 422

        return feedback_to_data(problem.root_feedback)

    post_parser = reqparse.RequestParser()
    post_parser.add_argument('name', type=str, required=True)
    post_parser.add_argument('description', type=str, required=False)
    post_parser.add_argument('score', type=int, required=False)
    post_parser.add_argument('parent', type=int, required=False)

    def post(self, problem_id):
        """Post a new feedback option

        Parameters
        ----------
            name: str
            description: str
            score: int
            parent: int
        """

        if (problem := Problem.query.get(problem_id)) is None:
            return dict(status=422, message=f"Problem with id #{problem_id} does not exist"), 422

        args = self.post_parser.parse_args()
        parent = FeedbackOption.query.get(args.parent)
        if parent is None:
            return dict(status=422, message=f"FeedbackOption with id #{args.parent} does not exist"), 422

        fb = FeedbackOption(problem=problem,
                            text=args.name,
                            description=args.description,
                            score=args.score,
                            parent=parent)
        db.session.add(fb)

        db.session.commit()

        return {
            'id': fb.id,
            'name': fb.text,
            'description': fb.description,
            'score': fb.score,
            'parent': fb.parent_id
        }

    put_parser = reqparse.RequestParser()
    put_parser.add_argument('id', type=int, required=True)
    put_parser.add_argument('name', type=str, required=True)
    put_parser.add_argument('description', type=str, required=False)
    put_parser.add_argument('score', type=int, required=False)
    put_parser.add_argument('exclusive', type=boolean, required=False)

    def put(self, problem_id):
        """Modify an existing feedback option

        Parameters
        ----------
            id: int
            name: str
            description: str
            score: int
        """

        args = self.put_parser.parse_args()

        if (fb := FeedbackOption.query.get(args.id)) is None:
            return dict(status=404, message=f"Feedback option with id #{args.id} does not exist"), 404

        if args.exclusive is not None:
            if len(fb.children) == 0:
                return dict(status=409,
                            message="Tryed to modify the exclusive property on a feedback option with no children"), 404
            if not fb.mut_excl_children and args.exclusive:  # we go from non-exclusive to exclusive
                # look at all solutions and ungrade those with inconsistencies
                ids = [f.id for f in fb.children]
                res = np.array(
                    db.session.query(solution_feedback.c.solution_id,
                                     func.count(solution_feedback.c.feedback_option_id))
                    .filter(solution_feedback.c.feedback_option_id.in_(ids))
                    .group_by(solution_feedback.c.solution_id).all())
                if len(res) > 0:
                    invalid_solutions = list(res[res[:, 1] > 1][:, 0])
                    updated_rows = db.session.query(Solution)\
                        .filter(Solution.id.in_(invalid_solutions))\
                        .update({Solution.grader_id: None, Solution.graded_at: None}, synchronize_session="fetch")

                    if len(invalid_solutions) != updated_rows:
                        return dict(status=404,
                                    message='Error changing the exclusive state.'), 404

            fb.mut_excl_children = args.exclusive

        fb.text = args.name
        fb.description = args.description
        fb.score = args.score

        db.session.commit()

        return {
            'id': fb.id,
            'name': fb.text,
            'description': fb.description,
            'score': fb.score,
            'parent': fb.parent_id
        }

    def delete(self, problem_id, feedback_id):
        """Delete an existing feedback option

        Parameters
        ----------
        problem_id : int
            The id of the problem to which the feedback belongs.
        feedback_id : int
            The database id of the feedback option.

        Notes
        -----
        We use the problem id for extra safety check that we don't corrupt
        things accidentally.
        """
        if (fb := FeedbackOption.query.get(feedback_id)) is None:
            return dict(status=404, message=f"Feedback option with id #{feedback_id} does not exist"), 404
        problem = fb.problem
        if problem.id != problem_id:
            return dict(status=400, message="Feedback option does not belong to this problem."), 400
        if fb.mc_option:
            return dict(status=405, message='Cannot delete feedback option'
                                            + ' attached to a multiple choice option.'), 405
        if fb.parent_id is None:
            return dict(status=405, message='Cannot delete root feedback option.'), 405

        # All feedback options, that are the child of the original feedback option will be deleted

        db.session.delete(fb)

        # If there are submissions with no feedback, we should mark them as
        # ungraded.
        solutions = Solution.query.filter(Solution.problem_id == problem_id,
                                          Solution.grader_id is not None).all()
        for solution in solutions:
            if solution.feedback_count == 0:
                solution.grader_id = None
                solution.graded_at = None

        db.session.commit()

        return dict(status=200, message=f"Feedback option with id {feedback_id} deleted."), 200
