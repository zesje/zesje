from flask import abort, Response

import numpy as np
import cv2

from ..images import get_box, guess_dpi
from ..database import Exam, Submission, Problem, Page, Solution
from ..pdf_generation import CHECKBOX_FORMAT
from ..scans import exam_student_id_widget


def get(exam_id, problem_id, submission_id, full_page=False):
    """get image for the given problem.

    Parameters
    ----------
    exam_id : int
    problem_id : int
    submission_id : int
        The copy number of the submission. This uniquely identifies
        the submission *within a given exam*.
    full_page : bool
        Whether to return a complete page

    Returns
    -------
    Image (JPEG mimetype)
    """
    exam = Exam.query.get(exam_id)
    if exam is None:
        abort(404, 'Exam does not exist.')

    problem = Problem.query.get(problem_id)
    if problem is None:
        abort(404, 'Problem does not exist.')

    sub = Submission.query.filter(Submission.exam_id == exam.id,
                                  Submission.copy_number == submission_id).one_or_none()
    if sub is None:
        abort(404, 'Submission does not exist.')

    widget_area = np.asarray([
        problem.widget.y,  # top
        problem.widget.y + problem.widget.height,  # bottom
        problem.widget.x,  # left
        problem.widget.x + problem.widget.width,  # right
    ])

    # TODO: use points as base unit
    widget_area_in = widget_area / 72

    #  get the page
    page = Page.query.filter(Page.submission_id == sub.id, Page.number == problem.widget.page).first()

    if page is None:
        abort(404, f'Page #{problem.widget.page} is missing for copy #{submission_id}.')

    page_path = page.path

    page_im = cv2.imread(page_path)

    dpi = guess_dpi(page_im)

    if exam.grade_anonymous and page.number == 0:
        student_id_widget, coords = exam_student_id_widget(exam.id)
        # coords are [ymin, ymax, xmin, xmax]
        page_im = _grey_out_student_widget(page_im, coords, dpi)

    # pregrade highliting
    solution = Solution.query.filter(Solution.submission_id == sub.id,
                                     Solution.problem_id == problem_id).one()

    fb = list(map(lambda x: x.id, solution.feedback))
    for option in problem.mc_options:
        if option.feedback_id in fb:
            x = int(option.x / 72 * dpi)
            y = int(option.y / 72 * dpi)
            box_length = int(CHECKBOX_FORMAT["box_size"] / 72 * dpi)
            x1 = x + box_length
            y1 = y + box_length
            page_im = cv2.rectangle(page_im, (x, y), (x1, y1), (0, 255, 0), 3)

    if not full_page:
        raw_image = get_box(page_im, widget_area_in, padding=0.3)
    else:
        raw_image = page_im

    image_encoded = cv2.imencode(".jpg", raw_image)[1].tostring()
    return Response(image_encoded, 200, mimetype='image/jpeg')


def _grey_out_student_widget(page_im, coords, dpi):
    """
    Grey out the student id widget on a page.
    Doesn't grey out the bottom left empty part of the widget,
    in case some exam material is there.

    :returns the page image with the widget greyed out

    """
    # coords are [ymin, ymax, xmin, xmax]
    grey = (150, 150, 150)
    coords = list(map(lambda c: int(c / 72 * dpi), coords))
    page_im = cv2.rectangle(page_im, (coords[2], coords[0]), (int(coords[3] / 2), coords[1]), grey, -1)
    height = coords[1] - coords[0]
    page_im = cv2.rectangle(page_im, (coords[2], coords[0]), (coords[3], int(coords[1] - height * 0.45)), grey, -1)
    return page_im
