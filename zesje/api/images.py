from flask import abort, Response, current_app

import cv2
import numpy as np

from ..images import get_box, guess_dpi, widget_area
from ..database import Exam, Submission, Problem, Page, Solution, Copy, ExamLayout
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
        Whether to return a complete page.
        If exam type is `unstructured` this option is ignored
            and the full page is always returned.

    Returns
    -------
    Image (JPEG mimetype)
    """
    if (exam := Exam.query.get(exam_id)) is None:
        abort(404, 'Exam does not exist.')

    if (problem := Problem.query.get(problem_id)) is None:
        abort(404, 'Problem does not exist.')

    if (sub := Submission.query.get(submission_id)) is None:
        abort(404, 'Submission does not exist.')

    pages = None
    if exam.layout == ExamLayout.unstructured:
        full_page = True

        if max(problem.widget.page for problem in exam.problems) == 0:
            # single paged exam, show all pages from all copies
            pages = Page.query.filter(Page.copy_id == Copy.id,
                                      Copy.submission == sub)\
                              .order_by(Page.number, Copy.number)\
                              .all()

    if not pages:
        page_number = problem.widget.page

        #  get the pages
        pages = Page.query.filter(Page.copy_id == Copy.id,
                                  Copy.submission == sub,
                                  Page.number == page_number)\
                          .order_by(Copy.number)\
                          .all()

    if len(pages) == 0:
        abort(404, f'Page #{page_number} is missing for all copies of submission #{submission_id}.')

    solution = Solution.query.filter(Solution.submission_id == sub.id,
                                     Solution.problem_id == problem_id).one()

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

    max_width = max(img.shape[1] for img in raw_images)

    if len(raw_images) == 1:
        stitched_image = raw_images[0]
    else:
        max_width = max(img.shape[1] for img in raw_images)

        resized_images = []
        for raw_image in raw_images:
            if max_width == raw_image.shape[1]:
                resized_images.append(raw_image)
            else:
                factor = max_width / raw_image.shape[1]
                new_height = int(factor * raw_image.shape[0])
                resized_images.append(cv2.resize(raw_image, (max_width, new_height)))

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
