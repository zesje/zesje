from flask.views import MethodView
from webargs import fields

from ._helpers import DBModel, use_args, use_kwargs
from ..database import db, MultipleChoiceOption, FeedbackOption, Problem


def update_mc_option(mc_option, args, feedback_id=None):
    """
    Updates a multiple choice option

    Parameters
    ----------
    mc_option : MultipleChoiceOption
        The multiple choice option
    args: dict
        The arguments supplied in the request body
    feedback_id : int
        id of the feedback option coupled to the multiple choice option
    """

    for attr, value in args.items():
        if value:
            setattr(mc_option, attr, value)

    if feedback_id:
        mc_option.feedback_id = feedback_id


class MultipleChoice(MethodView):

    @use_kwargs({'id': DBModel(MultipleChoiceOption)}, location='view_args')
    def get(self, id):
        """Fetches multiple choice option from the database

        Parameters
        ----------
        id: The ID of the multiple choice option in the database

        Returns
        -------
        A JSON object with the multiple choice option data
        """
        json = {
            'id': id.id,
            'name': id.name,
            'x': id.x,
            'y': id.y,
            'type': id.type,
            'feedback_id': id.feedback_id
        }

        # Nullable database fields
        if id.label:
            json['label'] = id.label

            return json

    @use_args({
        'name': fields.Str(required=False),
        'x': fields.Int(required=True),
        'y': fields.Int(required=True),
        'label': fields.Str(required=False),
        'problem': DBModel(Problem, required=True, data_key='problem_id')
    }, location='form')
    def put(self, args):
        """Adds a multiple choice option to the database

        For each new multiple choice option, a feedback option that links to
        the multiple choice option is inserted into the database. The new
        feedback option also refers to same problem as the MultipleChoiceOption
        """
        # Get request arguments
        label = args['label']
        problem = args['problem']

        if problem.exam.finalized:
            return dict(status=405, message='Cannot create multiple choice option and corresponding feedback option'
                        + ' in a finalized exam.'), 405

        # Insert new empty feedback option that links to the same problem
        new_feedback_option = FeedbackOption(problem_id=problem.id, text=label,
                                             description='', score=0, parent=problem.root_feedback)
        db.session.add(new_feedback_option)
        db.session.commit()

        args.pop('problem')

        # Insert new multiple choice entry into the database
        mc_entry = MultipleChoiceOption(**args, feedback_id=new_feedback_option.id)

        db.session.add(mc_entry)
        db.session.commit()

        return dict(status=200, mult_choice_id=mc_entry.id, feedback_id=new_feedback_option.id,
                    message=f'New multiple choice question with id {mc_entry.id} inserted. '
                    + f'New feedback option with id {new_feedback_option.id} inserted.'), 200

    @use_kwargs({'id': DBModel(MultipleChoiceOption)}, location='view_args')
    @use_args({
        'name': fields.Str(required=False),
        'x': fields.Int(required=False),
        'y': fields.Int(required=False),
        'label': fields.Str(required=False),
    }, location='form')
    def patch(self, args, id):
        """
        Updates a multiple choice option

        Parameters
        ----------
            id: The id of the multiple choice option in the database.
        """
        if id.feedback.problem.exam.finalized:
            return dict(status=405, message='Exam is finalized'), 405

        update_mc_option(id, args)

        db.session.commit()

        return dict(status=200, message=f'Multiple choice question with id {id.id} updated'), 200

    @use_kwargs({'id': DBModel(MultipleChoiceOption)}, location='view_args')
    def delete(self, id):
        """Deletes a multiple choice option from the database.
        Also deletes the associated feedback option with this multiple choice option.

        An error will be thrown if the user tries to delete a feedback option
        associated with a multiple choice option in a finalized exam.

        Parameters
        ----------
            id: The ID of the multiple choice option in the database

        Returns
        -------
            A message indicating success or failure
        """
        # Check if the exam is finalized, do not delete the multiple choice option otherwise
        if id.feedback.problem.exam.finalized:
            return dict(status=405, message='Cannot delete multiple choice option in a finalized exam.'), 405

        db.session.delete(id)
        db.session.commit()

        return dict(status=200, mult_choice_id=id.id, feedback_id=id.feedback_id,
                    message=f'Multiple choice question with id {id.id} deleted.'
                    + f'Feedback option with id {id.feedback_id} deleted.'), 200
