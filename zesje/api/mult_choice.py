from flask.views import MethodView

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

    put_parser = reqparse.RequestParser()

    # Arguments that can be supplied in the request body
    put_parser.add_argument('name', type=str, required=False)
    put_parser.add_argument('x', type=int, required=True)
    put_parser.add_argument('y', type=int, required=True)
    put_parser.add_argument('label', type=str, required=False)
    put_parser.add_argument('problem_id', type=int, required=True)  # Used for FeedbackOption

    def put(self):
        """Adds a multiple choice option to the database

        For each new multiple choice option, a feedback option that links to
        the multiple choice option is inserted into the database. The new
        feedback option also refers to same problem as the MultipleChoiceOption
        """
        args = self.put_parser.parse_args()

        # Get request arguments
        label = args['label']
        problem_id = args['problem_id']

        if not (problem := Problem.query.get(problem_id)):
            return dict(status=404, message=f'Problem with id {problem_id} does not exist'), 404

        if problem.exam.finalized:
            return dict(status=405, message='Cannot create multiple choice option and corresponding feedback option'
                        + ' in a finalized exam.'), 405

        # Insert new empty feedback option that links to the same problem
        new_feedback_option = FeedbackOption(problem_id=problem_id, text=label,
                                             description='', score=0, parent=problem.root_feedback)
        db.session.add(new_feedback_option)
        db.session.commit()

        args.pop('problem_id')

        # Insert new multiple choice entry into the database
        mc_entry = MultipleChoiceOption(**args, feedback_id=new_feedback_option.id)

        db.session.add(mc_entry)
        db.session.commit()

        return dict(status=200, mult_choice_id=mc_entry.id, feedback_id=new_feedback_option.id,
                    message=f'New multiple choice question with id {mc_entry.id} inserted. '
                    + f'New feedback option with id {new_feedback_option.id} inserted.'), 200

    def get(self, id):
        """Fetches multiple choice option from the database

        Parameters
        ----------
            id: The ID of the multiple choice option in the database

        Returns
        -------
            A JSON object with the multiple choice option data
        """

        if (mult_choice := MultipleChoiceOption.query.get(id)) is None:
            return dict(status=404, message=f'Multiple choice option with id {id} does not exist.'), 404

        json = {
            'id': mult_choice.id,
            'name': mult_choice.name,
            'x': mult_choice.x,
            'y': mult_choice.y,
            'type': mult_choice.type,
            'feedback_id': mult_choice.feedback_id
        }

        # Nullable database fields
        if mult_choice.label:
            json['label'] = mult_choice.label

        return json

    patch_parser = reqparse.RequestParser()

    # Arguments that have to be supplied in the request body
    patch_parser.add_argument('name', type=str, required=False)
    patch_parser.add_argument('x', type=int, required=False)
    patch_parser.add_argument('y', type=int, required=False)
    patch_parser.add_argument('label', type=str, required=False)

    def patch(self, id):
        """
        Updates a multiple choice option

        Parameters
        ----------
            id: The id of the multiple choice option in the database.
        """
        args = self.patch_parser.parse_args()

        if (mc_entry := MultipleChoiceOption.query.get(id)) is None:
            return dict(status=404, message=f"Multiple choice question with id {id} does not exist"), 404

        if mc_entry.feedback.problem.exam.finalized:
            return dict(status=405, message='Exam is finalized'), 405

        update_mc_option(mc_entry, args)

        db.session.commit()

        return dict(status=200, message=f'Multiple choice question with id {id} updated'), 200

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

        if (mult_choice := MultipleChoiceOption.query.get(id)) is None:
            return dict(status=404, message=f'Multiple choice question with id {id} does not exist.'), 404

        # Check if the exam is finalized, do not delete the multiple choice option otherwise
        exam = mult_choice.feedback.problem.exam

        if exam.finalized:
            return dict(status=405, message='Cannot delete multiple choice option in a finalized exam.'), 405

        db.session.delete(mult_choice)
        db.session.commit()

        return dict(status=200, mult_choice_id=id, feedback_id=mult_choice.feedback_id,
                    message=f'Multiple choice question with id {id} deleted.'
                    + f'Feedback option with id {mult_choice.feedback_id} deleted.'), 200
