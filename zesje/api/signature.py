from flask import abort, Response

import numpy as np
import cv2

from ..images import get_box
from ..database import Exam, Copy
from ..scans import exam_student_id_widget


def get(exam_id, copy_number):
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
    exam = Exam.query.get(exam_id)
    if exam is None:
        return dict(status=404, message='Exam does not exist.'), 404

    copy = Copy.query.filter(Copy.exam == exam,
                             Copy.number == copy_number).one_or_none()
    if copy is None:
        return dict(status=404, message='Copy does not exist.'), 404

    _, student_id_widget_coords = exam_student_id_widget(exam_id)
    widget_area = np.asarray(student_id_widget_coords)

    # TODO: use points as base unit
    widget_area_in = widget_area / 72

    try:
        first_page_path = next(p.abs_path for p in copy.pages if p.number == 0)
    except StopIteration:
        abort(404)
    first_page_im = cv2.imread(first_page_path)

    raw_image = get_box(first_page_im, widget_area_in, padding=0.3)
    image_encoded = cv2.imencode(".jpg", raw_image)[1].tostring()
    return Response(image_encoded, 200, mimetype='image/jpeg')
