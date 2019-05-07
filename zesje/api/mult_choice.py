from flask_restful import Resource

from ..database import db, MultipleChoiceOption


class MultipleChoice(Resource):

    def put(self, id, x, y, label, problem_id, feedback_id):
        """Adds a multiple choice option to the database

        Parameters
        ----------
            id: The id of the option
            x: the x-location of the the option in pixels
            y: the y-location of the the option in pixels
            label: The label of the option, this is a single char
            problem_id: Question to which this option is linked
            feedback_id: Feedback to which this option is linked
        """
        mc_entry = MultipleChoiceOption(id=id, x=x, y=y, label=label, problem_id=problem_id, feedback_id=feedback_id)
        db.session.add(mc_entry)

        db.session.commit()

        return dict(status=200, message="ok"), 200

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

        return {
            "id": mult_choice.id,
            "x": mult_choice.x,
            "y": mult_choice.y,
            "label": mult_choice.label,
            "problem_id": mult_choice.problem_id,
            "feedback_id": mult_choice.feedback_id
        }
