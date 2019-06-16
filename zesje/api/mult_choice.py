from flask_restful import Resource, reqparse

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

    mc_option.type = 'mcq_widget'


class MultipleChoice(Resource):

    put_parser = reqparse.RequestParser()

    # Arguments that have to be supplied in the request body
    put_parser.add_argument('name', type=str, required=True)
    put_parser.add_argument('x', type=int, required=True)
    put_parser.add_argument('y', type=int, required=True)
    put_parser.add_argument('label', type=str, required=False)
    put_parser.add_argument('fb_description', type=str, required=False)
    put_parser.add_argument('fb_score', type=str, required=False)
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
        fb_description = args['fb_description']
        fb_score = args['fb_score']
        problem_id = args['problem_id']

        if not Problem.query.get(problem_id):
            return dict(status=404, message=f'Problem with id {problem_id} does not exist'), 404

        # Insert new empty feedback option that links to the same problem
        new_feedback_option = FeedbackOption(problem_id=problem_id, text=label,
                                             description=fb_description, score=fb_score)
        db.session.add(new_feedback_option)
        db.session.commit()

        # Insert new entry into the database
        mc_entry = MultipleChoiceOption()
        try:
            update_mc_option(mc_entry, args, new_feedback_option.id)
        except (TypeError, ValueError) as error:
            return dict(status=400, message=str(error)), 400

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
        mult_choice = MultipleChoiceOption.query.get(id)

        if not mult_choice:
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
            id: The id of the multiple choice option in the database.s
        """
        args = self.patch_parser.parse_args()

        mc_entry = MultipleChoiceOption.query.get(id)

        if not mc_entry:
            return dict(status=404, message=f"Multiple choice question with id {id} does not exist"), 404

        try:
            update_mc_option(mc_entry, args)
        except (TypeError, ValueError) as error:
            return dict(status=400, message=str(error)), 400

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
        mult_choice = MultipleChoiceOption.query.get(id)

        if not mult_choice:
            return dict(status=404, message=f'Multiple choice question with id {id} does not exist.'), 404

        # Check if the exam is finalized, do not delete the multiple choice option otherwise
        exam = mult_choice.feedback.problem.exam

        if exam.finalized:
            return dict(status=401, message='Cannot delete feedback option'
                        + ' attached to a multiple choice option in a finalized exam.'), 401

        db.session.delete(mult_choice)
        db.session.commit()

        return dict(status=200, mult_choice_id=id, feedback_id=mult_choice.feedback_id,
                    message=f'Multiple choice question with id {id} deleted.'
                    + f'Feedback option with id {mult_choice.feedback_id} deleted.'), 200
