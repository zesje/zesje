from flask_restful import Resource

from ..database import db, MultipleChoiceOption


class MultipleChoice(Resource):

    def put(self, id, x, y, label, problem_id, feedback_id):
        mc_entry = MultipleChoiceOption(id=id, x=x, y=y, label=label, problem_id=problem_id, feedback_id=feedback_id)
        db.session.add(mc_entry)

        db.session.commit()

        return dict(status=200, message="ok"), 200
