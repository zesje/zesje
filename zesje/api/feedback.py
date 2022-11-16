""" REST api for problems """
from flask.views import MethodView
from webargs import fields
from sqlalchemy import func
import numpy as np

from ._helpers import DBModel, ApiValidationError, non_empty_string, use_args, use_kwargs
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

    @use_kwargs({'problem': DBModel(Problem, required=True)})
    def get(self, problem):
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
        return feedback_to_data(problem.root_feedback)

    @use_kwargs({'problem': DBModel(Problem, required=True)})
    @use_args({
        'text': fields.Str(required=True, validate=non_empty_string, data_key='name'),
        'description': fields.Str(required=False),
        'score': fields.Int(required=False),
        'parent': DBModel(FeedbackOption, required=False, data_key='parentId')
    }, location='json')
    def post(self, args, problem):
        """Post a new feedback option

        Parameters
        ----------
            name: str
            description: str
            score: int
            parent: int
        """
        fb = FeedbackOption(problem=problem, **args)
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
        'problem': DBModel(Problem, required=True),
        'feedback': DBModel(FeedbackOption, required=True)
    })
    @use_args({
        'text': fields.Str(required=False, validate=non_empty_string, data_key='name'),
        'description': fields.Str(required=False),
        'score': fields.Int(required=False),
        'exclusive': fields.Bool(required=False, load_default=None)
    }, location='json')
    def patch(self, args, problem, feedback):
        """Modify an existing feedback option

        Parameters
        ----------
            id: int
            name: str
            description: str
            score: int
        """
        set_aside_solutions = 0

        if (exclusive := args.pop('exclusive')) is not None:
            if len(feedback.children) == 0:
                return dict(status=409,
                            message="Tryed to modify the exclusive property on a feedback option with no children"), 409
            if not feedback.mut_excl_children and exclusive:  # we go from non-exclusive to exclusive
                # look at all solutions and ungrade those with inconsistencies
                ids = [f.id for f in feedback.children]
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

            feedback.mut_excl_children = exclusive

        for attr, value in args.items():
            setattr(feedback, attr, value)

        db.session.commit()

        return dict(status=200,
                    feedback=feedback_to_data(feedback, full_children=False),
                    set_aside_solutions=set_aside_solutions), 200

    @use_kwargs({
        'problem': DBModel(Problem, required=True),
        'feedback': DBModel(FeedbackOption, required=True, validate_model=[
            lambda fb: fb.parent_id is not None or ApiValidationError('Cannot delete root feedback option.', 405),
            lambda fb: not fb.mc_option or
                ApiValidationError('Cannot delete feedback option attached to a multiple choice option.', 405)])
    })
    def delete(self, problem, feedback):
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
        if feedback.problem.id != problem.id:
            return dict(status=400, message="Feedback option does not belong to this problem."), 400

        # All feedback options, that are the child of the original feedback option will be deleted
        if len(feedback.parent.children) == 1 and feedback.parent.mut_excl_children:
            # we are about to delete the only child of a parent option that has exclusive enabled
            feedback.parent.mut_excl_children = False

        db.session.delete(feedback)

        # If there are submissions with no feedback, we should mark them as
        # ungraded.
        solutions = Solution.query.filter(Solution.problem_id == problem.id,
                                          Solution.grader_id is not None).all()
        for solution in solutions:
            if solution.feedback_count == 0:
                solution.grader_id = None
                solution.graded_at = None

        db.session.commit()

        return dict(status=200, message=f"Feedback option with id {feedback.id} deleted."), 200
