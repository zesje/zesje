from flask import abort, Response, current_app

import cv2
import numpy as np

from ..images import get_box, guess_dpi, widget_area
from ..database import Exam, Submission, Problem, Page, Solution, Copy
from ..scans import exam_student_id_widget


def get(exam_id, problem_id, submission_id, full_page=False):
    """get image for the given problem.

    Parameters
    ----------
    exam_id : int
    problem_id : int
    submission_id : int
        The id of the submission. This uniquely identifies
        the submission *across all exams*.
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

    sub = Submission.query.get(submission_id)
    if sub is None:
        abort(404, 'Submission does not exist.')

    # TODO: use points as base unit
    widget_area_in = widget_area(problem)
    page_number = problem.widget.page

    #  get the pages
    pages = Page.query.filter(Page.copy_id == Copy.id,
                              Copy.submission == sub,
                              Page.number == page_number).all()

    if len(pages) != len(sub.copies):
        abort(404, f'Page #{page_number} is missing for some copies of submission #{submission_id}.')

    solution = Solution.query.filter(Solution.submission_id == sub.id,
                                     Solution.problem_id == problem_id).one()

    if exam.grade_anonymous and page_number == 0:
        student_id_widget, coords = exam_student_id_widget(exam.id)

    raw_images = []

    for page in pages:
        page_path = page.abs_path
        page_im = cv2.imread(page_path)
        dpi = guess_dpi(page_im)

        if exam.grade_anonymous and page_number == 0:
            # coords are [ymin, ymax, xmin, xmax]
            page_im = _grey_out_student_widget(page_im, coords, dpi)

        # pregrade highlighting
        fb = list(map(lambda x: x.id, solution.feedback))
        for option in problem.mc_options:
            if option.feedback_id in fb:
                x = int(option.x / 72 * dpi)
                y = int(option.y / 72 * dpi)
                box_length = int(current_app.config['CHECKBOX_SIZE'] / 72 * dpi)
                x1 = x + box_length
                y1 = y + box_length
                page_im = cv2.rectangle(page_im, (x, y), (x1, y1), (0, 255, 0), 3)

        if not full_page:
            raw_image = get_box(page_im, widget_area_in, padding=0.3)
        else:
            raw_image = page_im

        raw_images.append(raw_image)

    max_height = max(img.shape[0] for img in raw_images)
    max_width = max(img.shape[1] for img in raw_images)

    if len(raw_images) == 1:
        stitched_image = raw_images[0]
    else:
        resized_images = (cv2.resize(raw_image, (max_width, max_height)) for raw_image in raw_images)
        stitched_image = np.concatenate(tuple(resized_images), axis=0)

    image_encoded = cv2.imencode(".jpg", stitched_image)[1].tostring()
    return Response(image_encoded, 200, mimetype='image/jpeg')


def _grey_out_student_widget(page_im, coords, dpi):
    """
    Grey out the student id widget on a page.
    Doesn't grey out the bottom left empty part of the widget,
    in case some exam material is there.

    :returns the page image with the widget greyed out

    """
    grey = (150, 150, 150)
    ymin, ymax, xmin, xmax = (np.array(coords) / 72 * dpi).astype(int)
    height, width = ymax - ymin, xmax - xmin

    xmiddle = int(xmin + 0.5 * width)
    ymiddle = int(ymin + 0.55 * height)

    page_im = cv2.rectangle(page_im, (xmin, ymin), (xmiddle, ymax), grey, -1)
    page_im = cv2.rectangle(page_im, (xmiddle, ymin), (xmax, ymiddle), grey, -1)
    return page_im
