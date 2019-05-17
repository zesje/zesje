from flask_restful import Resource, reqparse

from ..database import db, MultipleChoiceOption


def set_mc_data(mc_entry, name, x, y, mc_type, problem_id, feedback_id, label):
    """Sets the data of a MultipleChoiceOption ORM object.

    Parameters:
    -----------
    mc_entry: The MultipleChoiceOption object
    x: the x-position of the MultipleChoiceOption object.
    y: the y-position of the MultipleChoiceOption object.
    problem_id: the problem the MultipleChoiceOption refers to
    feedback_id: the feedback the MultipleChoiceOption refers to
    label: label for the checkbox that this MultipleChoiceOption represents
    """
    mc_entry.name = name
    mc_entry.x = x
    mc_entry.y = y
    mc_entry.type = mc_type
    mc_entry.problem_id = problem_id
    mc_entry.feedback_id = feedback_id
    mc_entry.label = label


class MultipleChoice(Resource):

    put_parser = reqparse.RequestParser()

    # Arguments that have to be supplied in the request body
    put_parser.add_argument('name', type=str, required=True)
    put_parser.add_argument('x', type=int, required=True)
    put_parser.add_argument('y', type=int, required=True)
    put_parser.add_argument('label', type=str, required=False)
    put_parser.add_argument('problem_id', type=int, required=True)
    put_parser.add_argument('feedback_id', type=int, required=False)

    def put(self, id=None):
        """Adds or updates a multiple choice option to the database

        If the parameter id is not present, a new multiple choice question
        will be inserted with the data provided in the request body.

        Parameters
        ----------
            id: The id of the multiple choice option
        """

        args = self.put_parser.parse_args()

        # Get request arguments
        name = args['name']
        x = args['x']
        y = args['y']
        label = args['label']
        problem_id = args['problem_id']
        feedback_id = args['feedback_id']

        # TODO: Set type here or add to request?
        mc_type = 'mcq_widget'

        if not id:
            # Insert new entry into the database
            mc_entry = MultipleChoiceOption()
            set_mc_data(mc_entry, name, x, y, mc_type, problem_id, feedback_id, label)

            db.session.add(mc_entry)
            db.session.commit()

            return dict(status=200, message=f'New multiple choice question with id {mc_entry.id} inserted', mc_id=mc_entry.id), 200

        # Update existing entry otherwise
        mc_entry = MultipleChoiceOption.query.get(id)

        if not mc_entry:
            return dict(status=404, message=f"Multiple choice question with id {id} does not exist"), 404

        set_mc_data(mc_entry, name, x, y, mc_type, problem_id, feedback_id, label)
        db.session.commit()

        return dict(status=200, message=f'Multiple choice question with id {id} updated'), 200

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
            return dict(status=404, message=f'Multiple choice question with id {id} does not exist.'), 404

        json = {
            'id': mult_choice.id,
            'name': mult_choice.name,
            'x': mult_choice.x,
            'y': mult_choice.y,
            'type': mult_choice.type,
            'problem_id': mult_choice.problem_id
        }

        # Nullable database fields
        if mult_choice.label:
            json['label'] = mult_choice.label

        if mult_choice.feedback_id:
            json['feedback_id'] = mult_choice.feedback_id

        return json
