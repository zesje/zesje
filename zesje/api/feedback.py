""" REST api for problems """
from flask.views import MethodView
from webargs import fields
from sqlalchemy import func
import numpy as np

from ._helpers import DBModel, non_empty_string, use_args, use_kwargs
from ..database import db, Problem, FeedbackOption, Solution, solution_feedback


def feedback_to_data(feedback, full_children=True):
    return {
        'id': feedback.id,
        'name': feedback.text,
        'description': feedback.description,
        'score': feedback.score,
        'parent': feedback.parent_id,
        'used':
            db.session.query(solution_feedback).filter(solution_feedback.c.feedback_option_id == feedback.id).count(),
        'children': [feedback_to_data(child) if full_children else child.id for child in feedback.children],
        'exclusive': feedback.mut_excl_children
    }


class Feedback(MethodView):
    """ List of feedback options of a problem """

    @use_kwargs({'problem_id': DBModel(Problem, required=True)}, location='view_args')
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
        return feedback_to_data(problem_id.root_feedback)

    @use_kwargs({'problem_id': DBModel(Problem, required=True)}, location='view_args')
    @use_args({
        'name': fields.Str(required=True, validate=non_empty_string),
        'description': fields.Str(required=False),
        'score': fields.Int(required=False),
        'parentId': DBModel(FeedbackOption, required=False)
    }, location='form')
    def post(self, args, problem_id):
        """Post a new feedback option

        Parameters
        ----------
            name: str
            description: str
            score: int
            parent: int
        """
        fb = FeedbackOption(problem=problem_id,
                            text=args['name'],
                            description=args['description'],
                            score=args['score'],
                            parent=args['parentId'])
        db.session.add(fb)
        db.session.commit()

        return {
            'id': fb.id,
            'name': fb.text,
            'description': fb.description,
            'score': fb.score,
            'parent': fb.parent_id
        }

    @use_kwargs({
        'problem_id': DBModel(Problem, required=True),
        'feedback_id': DBModel(FeedbackOption, required=True)
    }, location='view_args')
    @use_args({
        'name': fields.Str(required=False, missing=None),
        'description': fields.Str(required=False, missing=None),
        'score': fields.Int(required=False, missing=None),
        'exclusive': fields.Bool(required=False, missing=None)
    }, location='form')
    def patch(self, args, problem_id, feedback_id):
        """Modify an existing feedback option

        Parameters
        ----------
            id: int
            name: str
            description: str
            score: int
        """
        set_aside_solutions = 0

        if args['exclusive'] is not None:
            if len(feedback_id.children) == 0:
                return dict(status=409,
                            message="Tryed to modify the exclusive property on a feedback option with no children"), 409
            if not feedback_id.mut_excl_children and args['exclusive']:  # we go from non-exclusive to exclusive
                # look at all solutions and ungrade those with inconsistencies
                ids = [f.id for f in feedback_id.children]
                res = np.array(
                    db.session.query(solution_feedback.c.solution_id,
                                     func.count(solution_feedback.c.feedback_option_id))
                    .filter(solution_feedback.c.feedback_option_id.in_(ids))
                    .group_by(solution_feedback.c.solution_id).all())
                if len(res) > 0:
                    invalid_solutions = list(res[res[:, 1] > 1][:, 0])
                    set_aside_solutions = db.session.query(Solution)\
                        .filter(Solution.id.in_(invalid_solutions))\
                        .update({Solution.grader_id: None, Solution.graded_at: None}, synchronize_session="fetch")

                    if len(invalid_solutions) != set_aside_solutions:
                        return dict(status=404,
                                    message='Error changing the exclusive state of '
                                            f'({len(invalid_solutions) - set_aside_solutions} solutions.'), 404

            feedback_id.mut_excl_children = args['exclusive']

        if args['name'] is not None:
            if (name := args['name'].strip()):
                feedback_id.text = name
            else:
                return dict(status=409, message="Feedback Option name cannot be empty."), 409

        if args['score'] is not None:
            feedback_id.score = args['score']

        if args['description'] is not None:
            feedback_id.description = args['description']

        db.session.commit()

        return dict(status=200,
                    feedback=feedback_to_data(feedback_id, full_children=False),
                    set_aside_solutions=set_aside_solutions), 200

    @use_kwargs({
        'problem_id': DBModel(Problem, required=True),
        'feedback_id': DBModel(FeedbackOption, required=True)
    }, location='view_args')
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
        if feedback_id.problem.id != problem_id.id:
            return dict(status=400, message="Feedback option does not belong to this problem."), 400
        if feedback_id.mc_option:
            return dict(status=405, message='Cannot delete feedback option'
                                            + ' attached to a multiple choice option.'), 405
        if feedback_id.parent_id is None:
            return dict(status=405, message='Cannot delete root feedback option.'), 405

        # All feedback options, that are the child of the original feedback option will be deleted
        if len(feedback_id.parent.children) == 1 and feedback_id.parent.mut_excl_children:
            # we are about to delete the only child of a parent option that has exclusive enabled
            feedback_id.parent.mut_excl_children = False

        db.session.delete(feedback_id)

        # If there are submissions with no feedback, we should mark them as
        # ungraded.
        solutions = Solution.query.filter(Solution.problem_id == problem_id.id,
                                          Solution.grader_id is not None).all()
        for solution in solutions:
            if solution.feedback_count == 0:
                solution.grader_id = None
                solution.graded_at = None

        db.session.commit()

        return dict(status=200, message=f"Feedback option with id {feedback_id.id} deleted."), 200
