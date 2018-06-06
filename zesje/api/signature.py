from flask import abort, Response, current_app as app

from pony import orm
import numpy as np
import cv2

from ..helpers import image_helper
from ..database import Exam, Submission


@orm.db_session
def get(exam_id, submission_id):
    """get student signature for the given submission.

    Parameters
    ----------
    exam_id : int
    submission_id : int
        The copy number of the submission. This uniquely identifies
        the submission *within a given exam*.

    Returns
    -------
    Image (JPEG mimetype)
    """
    # We could register an app-global error handler for this,
    # but it would add more code then it removes.
    exam = Exam.get(id=exam_id)
    if not exam:
        abort(404)
    sub = Submission.get(exam=exam, copy_number=submission_id)
    if not sub:
        abort(404)

    student_id_widget = next(
        widget
        for widget
        in exam.widgets
        if widget.name == 'student_id_widget'
    )

    widget_area = np.asarray([
        student_id_widget.y,  # top
        student_id_widget.y + app.config.get('ID_GRID_HEIGHT', 181),  # bottom
        student_id_widget.x,  # left
        student_id_widget.x + app.config.get('ID_GRID_WIDTH', 313),  # right
    ])

    # TODO: use points as base unit
    widget_area_in = widget_area / 72

    #  get first page
    #  TODO: is this a reliable way to get the first page?
    first_page_path = next(p.path for p in sub.pages if 'page00.jpg' in p.path)
    first_page_im = cv2.imread(first_page_path)

    raw_image = image_helper.get_box(
        first_page_im,
        widget_area_in,
        padding=0.3,
    )
    image_encoded = cv2.imencode(".jpg", raw_image)[1].tostring()
    return Response(image_encoded, 200, mimetype='image/jpeg')
