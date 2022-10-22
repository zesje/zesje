from flask import abort, Response, current_app, request
from webargs import fields
from pathlib import Path
from werkzeug.http import parse_date, http_date
from datetime import datetime

import cv2
import numpy as np

from ._helpers import DBModel, use_kwargs
from ..images import get_box, guess_dpi, widget_area
from ..database import Exam, Submission, Problem, Page, Solution, Copy, ExamLayout
from ..scans import exam_student_id_widget


@use_kwargs({
    'exam_id': DBModel(Exam, required=True),
    'problem_id': DBModel(Problem, required=True),
    'submission_id': DBModel(Submission, required=True),
    'full_page': fields.Bool(required=False, load_default=0)
}, location='view_args')
def get(exam, problem, submission, full_page):
    """get image for the given problem.

    Parameters
    ----------
    exam_id : int
    problem_id : int
    submission_id : int
        The id of the submission. This uniquely identifies
        the submission *across all exams*.
    full_page : bool
        Whether to return a complete page.
        If exam type is `unstructured` this option is ignored
            and the full page is always returned.

    Returns
    -------
    Image (JPEG mimetype)
    """
    pages = None
    if exam.layout == ExamLayout.unstructured:
        full_page = True

        if max(problem.widget.page for problem in exam.problems) == 0:
            # single paged exam, show all pages from all copies
            pages = Page.query.filter(Page.copy_id == Copy.id,
                                      Copy.submission == submission)\
                              .order_by(Page.number, Copy.number)\
                              .all()

    if not pages:
        page_number = problem.widget.page

        #  get the pages
        pages = Page.query.filter(Page.copy_id == Copy.id,
                                  Copy.submission == submission,
                                  Page.number == page_number)\
                          .order_by(Copy.number)\
                          .all()

    if len(pages) == 0:
        abort(404, f'Page #{page_number} is missing for all copies of submission #{submission.id}.')

    # Convert to int to match the time resolution of HTTP headers (seconds)
    last_modified = int(max(Path(page.abs_path).stat().st_mtime for page in pages))

    if modified_since := request.headers.get('If-Modified-Since'):
        modified_since = parse_date(modified_since).timestamp()
        if last_modified == modified_since:
            # Send 304 Not Modified with empty body
            return '', 304

    solution = Solution.query.filter(Solution.submission_id == submission.id,
                                     Solution.problem_id == problem.id).one()

    if exam.layout == ExamLayout.templated and exam.grade_anonymous and page_number == 0:
        student_id_widget, coords = exam_student_id_widget(exam.id)
    else:
        student_id_widget = None

    raw_images = []

    # TODO: use points as base unit
    widget_area_in = widget_area(problem)

    for page in pages:
        page_path = page.abs_path
        page_im = cv2.imread(page_path)
        dpi = guess_dpi(page_im)

        if student_id_widget:
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

    if len(raw_images) == 1:
        stitched_image = raw_images[0]
    else:
        heights, widths = np.array([img.shape[:2] for img in raw_images]).T
        max_width = min(np.max(widths), current_app.config['MAX_WIDTH'])
        factors = max_width / widths
        height_factor = current_app.config['MAX_HEIGHT'] / np.sum(heights * factors)
        height_factor = min(height_factor, 1)
        max_width = int(max_width * height_factor)
        factors *= height_factor

        resized_images = []
        for raw_image, factor in zip(raw_images, factors):
            if max_width == raw_image.shape[1]:
                resized_images.append(raw_image)
                continue

            new_height = round(factor * raw_image.shape[0])
            resized_images.append(cv2.resize(raw_image, (max_width, new_height)))

        stitched_image = np.concatenate(tuple(resized_images), axis=0)

    image_encoded = cv2.imencode(".jpg", stitched_image)[1].tostring()

    headers = {
        'Last-Modified': http_date(datetime.fromtimestamp(last_modified)),
        'Cache-Control': 'no-cache'
    }
    return Response(image_encoded, 200, headers=headers, mimetype='image/jpeg')


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
