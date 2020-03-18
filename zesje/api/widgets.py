from flask_restful import Resource
from flask import current_app, request

from ..database import db, Widget, ExamWidget, MultipleChoiceOption
from ..constants import EXAM_WIDGET_SIZE, MARKER_MARGIN, PAGE_FORMATS, MARKER_LINE_WIDTH


def check_exam_widget_position(widget, params):
    """ Moves the exam widget if it overlaps with the corner marker margins. """

    if 'x' not in params:
        # position is not being changed
        return params, False

    size = EXAM_WIDGET_SIZE[widget.name]
    page_size = PAGE_FORMATS[current_app.config['PAGE_FORMAT']]
    margin = int(MARKER_MARGIN + MARKER_LINE_WIDTH)

    x = min(max(params['x'], margin), page_size[0] - size[0] - margin)
    y = min(max(params['y'], margin), page_size[1] - size[1] - margin)

    changed = x != params['x'] or y != params['y']
    params['x'] = x
    params['y'] = y

    return params, changed


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
        changed = False

        if isinstance(widget, ExamWidget):
            body, changed = check_exam_widget_position(widget, body)

        for attr, value in body.items():
            try:
                setattr(widget, attr, value)
            except AttributeError:
                msg = f"Widget doesn't have a property {attr}"
                return dict(status=400, message=msg), 400
            except (TypeError, ValueError) as error:
                return dict(status=400, message=str(error)), 400

        db.session.commit()

        if changed:
            # this forces the server to reload the widget position of it has been changed
            return dict(status=409,
                        message="The Exam widget has to lay between the corner markers region.",
                        widgetId=widget_id,
                        position={'x': body['x'], 'y': body['y']}), 409

        return dict(status=200, message="ok"), 200
