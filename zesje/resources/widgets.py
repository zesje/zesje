from flask_restful import Resource
from flask import request

from pony import orm

from ..models import db, Widget


class Widgets(Resource):

    @orm.db_session
    def patch(self, widget_id):

        widget = Widget.get(id=widget_id)

        if widget is None:
            msg = f"Widget with id {widget_id} doesn't exist"
            return dict(status=404, message=msg), 404

        # will 400 on malformed json
        data = request.get_json()

        for attr, value in data.items():
            # check before modifying
            if hasattr(widget, attr):
                setattr(widget, attr, value)
            else:
                msg = f"Widget doesn't have a property {attr}"
                return dict(status=400, message=msg), 400

        db.commit()

        return dict(status=200, message="ok"), 200

    @orm.db_session
    def delete(self, widget_id):

        widget = Widget.get(id=widget_id)

        if widget is None:
            msg = f"Widget with id {widget_id} doesn't exist"
            return dict(status=404, message=msg), 404
        elif widget.name in ['barcode_widget', 'student_id_widget']:
            msg = f"Widget with name {widget.name} is not deletable"
            return dict(status=403, message=msg), 403
        else:

            widget.delete()
            db.commit()

            return dict(status=200, message="ok"), 200
