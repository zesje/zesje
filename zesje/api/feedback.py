""" REST api for problems """

from flask_restful import Resource, reqparse

from pony import orm

from ..database import Problem, FeedbackOption


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
    post_parser.add_argument('description', type=str, required=False)
    post_parser.add_argument('score', type=int, required=False)

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

        fb = FeedbackOption(problem=problem, text=args.name, description=args.description, score=args.score)
        orm.commit()

        return {
            'id': fb.id,
            'name': fb.text,
            'description': fb.description,
            'score': fb.score
        }

    put_parser = reqparse.RequestParser()
    put_parser.add_argument('id', type=int, required=True)
    put_parser.add_argument('name', type=str, required=True)
    put_parser.add_argument('description', type=str, required=False)
    put_parser.add_argument('score', type=int, required=False)

    @orm.db_session
    def put(self, problem_id):
        """Modify an existing feedback option

        Parameters
        ----------
            id: int
            name: str
            description: str
            score: int
        """

        args = self.put_parser.parse_args()

        fb = FeedbackOption.get(id=args.id)
        if fb:
            fb.set(text=args.name, description=args.description, score=args.score)

        return {
            'id': fb.id,
            'name': fb.text,
            'description': fb.description,
            'score': fb.score
        }

    @orm.db_session
    def delete(self, problem_id, feedback_id):
        """Modify an existing feedback option

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
        fb = FeedbackOption.get(id=feedback_id)
        if fb is None:
            return dict(status=404, message="Feedback with this id does not exist"), 404
        elif fb.problem.id != problem_id:
            return dict(status=409, message="Feedback does not match the problem."), 409
        else:
            fb.delete()
