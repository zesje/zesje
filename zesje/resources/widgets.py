import sys

from flask_restful import Resource, reqparse

from pony import orm

from ..models import db, Exam, Widget

class Widgets(Resource):

    @orm.db_session
    def get(self, widget_id = None):
        """Get detailed information about a single widget

        URL Parameters
        --------------
        widget_id : int
            widget ID

        Returns
        -------
        id : int
            widget ID
        data : str
            data associated with the widget. Opaque to the server, client should
            know what to do.
        """

        widget = Widget[widget_id]

        return {
            'id': widget.id,
            'data': widget.data.decode("utf-8")
        }

    post_parser = reqparse.RequestParser()
    post_parser.add_argument('exam_id', type=int, required=True, location='form')
    post_parser.add_argument('data', type=str, required=True, location='form')

    @orm.db_session
    def post(self):
        """Add a new widget.

        Will error if exam for given id does not exist

        Parameters
        ----------
        exam_id : int
            id of the exam this widget should be associated with
        data : str
            data associated with the widget. Opaque to the server, client should
            know what to do.

        Returns
        -------
        id : int
            widget ID
        """

        args = self.post_parser.parse_args()

        exam_id = args['exam_id']
        data = args['data']

        exam = Exam.get(id=exam_id)

        if exam is None:
            msg = f"Exam with id {exam_id} doesn't exist"
            return dict(status=400, message=msg), 400

        widget = Widget(
            exam = exam_id,
            data = bytes(data, 'utf-8')
        )

        db.commit()

        return {
            'id': widget.id
        }


    @orm.db_session
    def delete(self, widget_id):

        widget = Widget.get(id=widget_id)

        if widget is None:
            msg = f"Widget with id {widget_id} doesn't exist"
            return dict(status=404, message=msg), 404
        else:

            widget.delete()
            db.commit()

            return dict(status=200, message="ok"), 200
