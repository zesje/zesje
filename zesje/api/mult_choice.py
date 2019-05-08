from flask_restful import Resource, reqparse

from ..database import db, MultipleChoiceOption


class MultipleChoice(Resource):

    put_parser = reqparse.RequestParser()

    # Arguments that have to be supplied in the request body
    put_parser.add_argument('x', type=int, required=True)
    put_parser.add_argument('y', type=int, required=True)
    put_parser.add_argument('page', type=int, required=True)
    put_parser.add_argument('label', type=str, required=False)
    put_parser.add_argument('problem_id', type=int, required=True)
    put_parser.add_argument('feedback_id', type=int, required=True)

    def put(self, id):
        """Puts a multiple choice option to the database

        If the specified ID is already present, the current option will be updated.

        Parameters
        ----------
            id: The id of the multiple choice option
        """

        args = self.put_parser.parse_args()

        x = args['x']
        y = args['y']
        label = args['label']
        problem_id = args['problem_id']
        feedback_id = args['feedback_id']
        page = args['page']

        mc_entry = MultipleChoiceOption.query.get(id)

        # If entry is not present insert
        if not mc_entry:
            mc_entry = MultipleChoiceOption(
                id=id,
                x=x,
                y=y,
                page=page,
                label=label,
                problem_id=problem_id,
                feedback_id=feedback_id
            )

            db.session.add(mc_entry)
            db.session.commit()

            return dict(status=200, message='Multiple choice question inserted'), 200

        # Otherwise, update current entry
        mc_entry.x = x
        mc_entry.y = y
        mc_entry.label = label
        mc_entry.problem_id = problem_id
        mc_entry.feedback_id = feedback_id
        mc_entry.page = page

        db.session.commit()

        return dict(status=200, message='Multiple choice question updated'), 200

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
            return dict(status=404, message='Multiple choice question does not exist.'), 404

        json = {
            "id": mult_choice.id,
            "x": mult_choice.x,
            "y": mult_choice.y,
            "problem_id": mult_choice.problem_id,
            "feedback_id": mult_choice.feedback_id
        }

        if mult_choice.label:
            json['label'] = mult_choice.label

        return json
