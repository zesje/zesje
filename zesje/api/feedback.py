""" REST api for problems """

from flask_restful import Resource, reqparse

from ..database import db, Problem, FeedbackOption, Solution


class Feedback(Resource):
    """ List of feedback options of a problem """

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

        if (problem := Problem.query.get(problem_id)) is None:
            return dict(status=404, message=f"Problem with id #{problem_id} does not exist"), 404

        return [
            {
                'id': fb.id,
                'name': fb.text,
                'description': fb.description,
                'score': fb.score,
                'used': len(fb.solutions)
            }
            for fb in FeedbackOption.query.filter(FeedbackOption.problem == problem)
        ]

    post_parser = reqparse.RequestParser()
    post_parser.add_argument('name', type=str, required=True)
    post_parser.add_argument('description', type=str, required=False)
    post_parser.add_argument('score', type=int, required=False)

    def post(self, problem_id):
        """Post a new feedback option

        Parameters
        ----------
            name: str
            description: str
            score: int
        """

        if (problem := Problem.query.get(problem_id)) is None:
            return dict(status=404, message=f"Problem with id #{problem_id} does not exist"), 404

        args = self.post_parser.parse_args()

        fb = FeedbackOption(problem=problem, text=args.name, description=args.description, score=args.score)
        db.session.add(fb)
        db.session.commit()

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

        if (fb := FeedbackOption.query.get(args.id)) is None:
            return dict(status=404, message=f"Feedback option with id #{args.id} does not exist"), 404

        fb.text = args.name
        fb.description = args.description
        fb.score = args.score

        db.session.commit()

        return {
            'id': fb.id,
            'name': fb.text,
            'description': fb.description,
            'score': fb.score
        }

    def delete(self, problem_id, feedback_id):
        """Delete an existing feedback option

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
        if (fb := FeedbackOption.query.get(feedback_id)) is None:
            return dict(status=404, message=f"Feedback option with id #{feedback_id} does not exist"), 404
        problem = fb.problem
        if problem.id != problem_id:
            return dict(status=400, message="Feedback option does not belong to this problem."), 400
        if fb.mc_option:
            return dict(status=403, message='Cannot delete feedback option'
                                            + ' attached to a multiple choice option.'), 403

        db.session.delete(fb)

        # If there are submissions with no feedback, we should mark them as
        # ungraded.
        solutions = Solution.query.filter(Solution.problem_id == problem_id,
                                          Solution.grader_id is not None).all()
        for solution in solutions:
            if solution.feedback_count == 0:
                solution.grader_id = None
                solution.graded_at = None

        db.session.commit()

        return dict(status=200, message=f"Feedback option with id {feedback_id} deleted."), 200
