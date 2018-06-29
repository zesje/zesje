""" REST api for problems """

from flask_restful import Resource, reqparse

from pony import orm

from ..database import db, Exam, Problem, ProblemWidget


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

    @orm.db_session
    def post(self):
        """Add a new problem.

        Will error if exam for given id does not exist
        Will 403 if exam is finalized

        """

        args = self.post_parser.parse_args()

        exam_id = args['exam_id']

        try:
            exam = Exam[exam_id]
        except orm.ObjectNotFound:
            msg = f"Exam with id {exam_id} doesn't exist"
            return dict(status=400, message=msg), 400
        else:
            if exam.finalized:
                return dict(status=403, message=f'Exam is finalized'), 403
            widget = ProblemWidget(
                x=args['x'],
                y=args['y'],
                width=args['width'],
                height=args['height'],
            )

            problem = Problem(
                exam=exam,
                name=args['name'],
                page=args['page'],
                widget=widget
            )

            db.commit()

            widget.name = f'problem_{problem.id}'

            return {
                'id': problem.id,
                'widget_id': widget.id,
            }

    put_parser = reqparse.RequestParser()
    put_parser.add_argument('name', type=str, required=True)

    @orm.db_session
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
        problem = Problem[problem_id]
        problem.name = name

        return dict(status=200, message="ok"), 200

    @orm.db_session
    def delete(self, problem_id):

        problem = Problem.get(id=problem_id)

        if problem is None:
            msg = f"Problem with id {problem_id} doesn't exist"
            return dict(status=404, message=msg), 404
        if problem.exam.finalized:
            return dict(status=403, message=f'Exam is finalized'), 403
        else:
            problem.delete()
            problem.widget.delete()
            db.commit()
            return dict(status=200, message="ok"), 200
