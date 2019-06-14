""" REST api for problems """

from flask_restful import Resource, reqparse

from ..database import db, Exam, Problem, ProblemWidget, Solution


class Problems(Resource):
    """ List of problems associated with a particular exam_id """

    post_parser = reqparse.RequestParser()
    post_parser.add_argument('exam_id', type=int, required=True, location='form')
    post_parser.add_argument('name', type=str, required=True, location='form')
    post_parser.add_argument('page', type=int, required=True, location='form')
    post_parser.add_argument('x', type=int, required=True, location='form')
    post_parser.add_argument('y', type=int, required=True, location='form')
    post_parser.add_argument('width', type=int, required=True, location='form')
    post_parser.add_argument('height', type=int, required=True, location='form')
    post_parser.add_argument('grading_policy', type=int, required=True, location='form')

    def post(self):
        """Add a new problem.

        Will error if exam for given id does not exist

        """

        args = self.post_parser.parse_args()

        exam_id = args['exam_id']

        exam = Exam.query.get(exam_id)
        if exam is None:
            msg = f"Exam with id {exam_id} doesn't exist"
            return dict(status=400, message=msg), 400
        else:
            widget = ProblemWidget(
                x=args['x'],
                y=args['y'],
                width=args['width'],
                height=args['height'],
                page=args['page'],
            )

            problem = Problem(
                exam=exam,
                name=args['name'],
                widget=widget,
                grading_policy=args['grading_policy']
            )

            # Widget is also added because it is used in problem
            db.session.add(problem)

            # Add solutions for each already existing submission
            for sub in exam.submissions:
                db.session.add(Solution(problem=problem, submission=sub))

            # Commit so problem gets an id
            db.session.commit()
            widget.name = f'problem_{problem.id}'

            db.session.commit()

            return {
                'id': problem.id,
                'widget_id': widget.id,
            }

    put_parser = reqparse.RequestParser()
    put_parser.add_argument('name', type=str)
    put_parser.add_argument('grading_policy', type=int)

    def put(self, problem_id, attr):
        """PUT to a problem

        This method accepts any of the legible arguments passed to it.

        problem_id: int
            the problem id to put to
        attr: str
            the attribute (or property) to put to

        Returns
            HTTP 200 on succes, 404 if problem is invalid
        """

        args = self.put_parser.parse_args()

        problem = Problem.query.get(problem_id)
        if problem is None:
            msg = f"Problem with id {problem_id} doesn't exist"
            return dict(status=404, message=msg), 404

        for key in args.keys():
            value = args[key]
            if value is not None:
                setattr(problem, key, value)

        db.session.commit()

        return dict(status=200, message="ok"), 200

    def delete(self, problem_id):

        problem = Problem.query.get(problem_id)

        if problem is None:
            msg = f"Problem with id {problem_id} doesn't exist"
            return dict(status=404, message=msg), 404
        if any([sol.graded_by is not None for sol in problem.solutions]):
            return dict(status=403, message=f'Problem has already been graded'), 403
        else:
            # Delete all solutions associated with this problem
            for sol in problem.solutions:
                db.session.delete(sol)
            # Delete all multiple choice options associated with this problem
            for mc_option in problem.mc_options:
                db.session.delete(mc_option)
            db.session.delete(problem.widget)
            db.session.delete(problem)
            db.session.commit()
            return dict(status=200, message="ok"), 200
