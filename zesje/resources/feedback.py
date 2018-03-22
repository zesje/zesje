""" REST api for problems """

from flask_restful import Resource, reqparse

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


    post_parser = reqparse.RequestParser()
    post_parser.add_argument('name', type=str, required=True)
    post_parser.add_argument('description', type=str, required=True)
    post_parser.add_argument('score', type=int, required=True)

    @orm.db_session
    def post(self, problem_id):
        """Post a new feedback option

        Parameters
        ----------
            name: str
            description: str
            score: int
        """

        problem = Problem[problem_id]

        args = self.post_parser.parse_args()

        fb = FeedbackOption(problem = problem, text = args.name, description = args.description, score = args.score)
        orm.commit();

        return  {
                    'id': fb.id,
                    'name': fb.text,
                    'description': fb.description,
                    'score': fb.score
                }
