from flask.views import MethodView
from flask import current_app, request

from ._helpers import DBModel, use_kwargs
from ..database import db, Widget, ExamWidget, MultipleChoiceOption, ExamLayout


def widget_to_data(widget):
    if isinstance(widget, ExamWidget):
        width, height = widget.size
    else:
        width, height = widget.width, widget.height

    return {
        'id': widget.id,
        'name': widget.name,
        'x': widget.x,
        'y': widget.y,
        'width': width,
        'height': height,
        'type': widget.type
    }


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


def normalise_pages(widgets):
    sorted_by_page = sorted(widgets, key=lambda w: w.page)

    prev_page = -1  # this ensures that the first page is correctly set to 0
    pages_to_substract = 0
    for widget in sorted_by_page:
        if prev_page < widget.page:
            # page changed, increment the number of pages to substact if the difference is bigger than one
            pages_to_substract += (widget.page - prev_page - 1)
            prev_page = widget.page

        widget.page -= pages_to_substract

    return pages_to_substract > 0


class Widgets(MethodView):

    @use_kwargs({'widget': DBModel(Widget, required=True)})
    def patch(self, widget):
        if isinstance(widget, ExamWidget) and widget.exam.finalized:
            return dict(status=409, message='Exam is finalized'), 409
        elif isinstance(widget, MultipleChoiceOption) and widget.feedback.problem.exam.finalized:
            return dict(status=409, message='Exam is finalized'), 409

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

        exam = widget.exam

        if exam.layout == ExamLayout.templated:
            name = 'Student ID' if widget.name == 'student_id_widget' else 'Barcode'
            message = f'The "{name}" widget has to lay between the corner markers region.'
            changed = force_boundaries(widget)
        elif exam.layout == ExamLayout.unstructured:
            message = "There can't be a gap in the page numbers"
            changed = normalise_pages(list(p.widget for p in exam.problems))
        else:
            message = "ok"
            changed = False

        db.session.commit()

        if changed:
            # this response forces the client to update the widget to the new state
            return dict(status=409,
                        message=message,
                        data=widget_to_data(widget)), 409

        return dict(status=200, message="ok"), 200
