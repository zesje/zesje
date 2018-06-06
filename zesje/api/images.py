import os

from flask import abort, Response

from pony import orm

import numpy as np
import cv2

from ..helpers import image_helper
from ..database import Exam, Submission, Problem


@orm.db_session
def get(exam_id, problem_id, submission_id):
    """get student signature for the given submission.

    Parameters
    ----------
    exam_id : int
    problem_id : int
    submission_id : int
        The copy number of the submission. This uniquely identifies
        the submission *within a given exam*.

    Returns
    -------
    Image (JPEG mimetype)
    """
    try:
        exam = Exam[exam_id]
        submission = Submission.get(exam=exam, copy_number=submission_id)
        problem = Problem[problem_id]
    except (KeyError, ValueError):
        abort(404)

    widget_area = np.asarray([
        problem.widget.y,  # top
        problem.widget.y + problem.widget.height,  # bottom
        problem.widget.x,  # left
        problem.widget.x + problem.widget.width,  # right
    ])

    # TODO: use points as base unit
    widget_area_in = widget_area / 72

    #  get the page
    page = f'page{problem.page:02d}.jpg'
    page_path = next(p.path for p in submission.pages if page == os.path.basename(p.path))

    page_im = cv2.imread(page_path)

    raw_image = image_helper.get_box(
        page_im,
        widget_area_in,
        padding=0.3,
    )
    image_encoded = cv2.imencode(".jpg", raw_image)[1].tostring()
    return Response(image_encoded, 200, mimetype='image/jpeg')
