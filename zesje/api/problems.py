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
    put_parser.add_argument('name', type=str, required=True)

    def put(self, problem_id, attr):
        """PUT to a problem

        As of writing this method only supports putting the name property

        problem_id: int
            the problem id to put to
        attr: str
            the attribute (or property) to put to (only supports 'name' now)

        Returns
            HTTP 200 on success
        """

        args = self.put_parser.parse_args()

        name = args['name']
        problem = Problem.query.get(problem_id)
        if problem is None:
            msg = f"Problem with id {problem_id} doesn't exist"
            return dict(status=404, message=msg), 404

        problem.name = name
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
            db.session.delete(problem)
            db.session.commit()
            return dict(status=200, message="ok"), 200
