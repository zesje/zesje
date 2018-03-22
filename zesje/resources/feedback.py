""" REST api for problems """

from flask_restful import Resource

from pony import orm

from ..models import Problem, FeedbackOption

class Feedback(Resource):
    """ List of feedback options of a problem """

    @orm.db_session
    def get(self, problem_id):
        """get list of feedback connected to a specific problem

        Returns
        -------
        list of:
            id: int
            name: str
            description: str
            score: int
            used: int
        """

        problem = Problem[problem_id]

        return [
            {
                'id': fb.id,
                'name': fb.text,
                'description': fb.description,
                'score': fb.score,
                'used': fb.solutions.count()
            }
            for fb in FeedbackOption.select(lambda fb: fb.problem == problem)
        ]
