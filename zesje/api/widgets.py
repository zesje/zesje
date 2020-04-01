from flask_restful import Resource
from flask import current_app, request

from ..database import db, Widget, ExamWidget, MultipleChoiceOption


def force_boundaries(widget):
    """ Moves the exam widget if it overlaps with the corner marker margins. """
    if not isinstance(widget, ExamWidget):
        return False

    size = widget.size
    page_size = current_app.config['PAGE_FORMATS'][current_app.config['PAGE_FORMAT']]
    margin = int(current_app.config['MARKER_MARGIN'] + current_app.config['MARKER_LINE_WIDTH'])

    x = min(max(widget.x, margin), page_size[0] - size[0] - margin)
    y = min(max(widget.y, margin), page_size[1] - size[1] - margin)

    if x != widget.x or y != widget.y:
        widget.x = x
        widget.y = y
        return True

    return False


class Widgets(Resource):

    def patch(self, widget_id):

        widget = Widget.query.get(widget_id)

        if widget is None:
            msg = f"Widget with id {widget_id} doesn't exist"
            return dict(status=404, message=msg), 404
        elif isinstance(widget, ExamWidget) and widget.exam.finalized:
            return dict(status=403, message=f'Exam is finalized'), 403
        elif isinstance(widget, MultipleChoiceOption) and widget.feedback.problem.exam.finalized:
            return dict(status=405, message=f'Exam is finalized'), 405

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

        changed = force_boundaries(widget)

        db.session.commit()

        if changed:
            # this response forces the client to move the widget to the specified position
            return dict(status=409,
                        message="The Exam widget has to lay between the corner markers region.",
                        widgetId=widget_id,
                        position={'x': widget.x, 'y': widget.y}), 409

        return dict(status=200, message="ok"), 200
