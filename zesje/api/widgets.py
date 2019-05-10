from flask_restful import Resource
from flask import request

from ..database import db, Widget, ExamWidget


class Widgets(Resource):

    def patch(self, widget_id):

        widget = Widget.query.get(widget_id)

        if widget is None:
            msg = f"Widget with id {widget_id} doesn't exist"
            return dict(status=404, message=msg), 404
        elif isinstance(widget, ExamWidget) and widget.exam.finalized:
            return dict(status=403, message=f'Exam is finalized'), 403

        # will 400 on malformed json
        body = request.get_json()

        for attr, value in body.items():
            try:
                setattr(widget, attr, value)
            except AttributeError:
                msg = f"Widget doesn't have a property {attr}"
                return dict(status=400, message=msg), 400
            except (TypeError, ValueError) as error:
                return dict(status=400, message=str(error)), 400

        db.session.commit()

        return dict(status=200, message="ok"), 200
