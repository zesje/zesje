""" REST api for problems """

from flask import request
from flask_restful import Resource, reqparse
from pony import orm

from ..models import db, Exam, Problem, ProblemWidget


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

        """

        args = self.post_parser.parse_args()

        exam_id = args['exam_id']

        try:
            exam = Exam[exam_id]
        except orm.ObjectNotFound:
            msg = f"Exam with id {exam_id} doesn't exist"
            return dict(status=400, message=msg), 400
        else:
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
    put_parser.add_argument('name', type=str, required=True, location='form')

    @orm.db_session
    def put(self, problem_id, attr):

        args = self.put_parser.parse_args()

        name = args['name']
        problem = Problem[problem_id]
        problem.name = name

        return dict(status=200, message="ok"), 200
