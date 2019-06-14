import cv2
import numpy as np
import os

from datetime import datetime

from .database import db, Solution, Grader, FeedbackOption, GradingPolicy
from .images import guess_dpi, get_box
from .blanks import set_blank

from PIL import Image
from flask import current_app


CHECKBOX_FORMAT = {
    "margin": 5,
    "font_size": 11,
    "box_size": 9
}


def add_feedback_to_solution(sub, exam, page, page_img):

    """
    Adds the multiple choice options that are identified as marked as a feedback option to a solution

    Parameters
    ------
    sub : Submission
        the current submission
    exam : Exam
        the current exam
    page_img : Image
        image of the page
    """
    problems_on_page = [problem for problem in exam.problems if problem.widget.page == page]

    for problem in problems_on_page:
        sol = Solution.query.filter(Solution.problem_id == problem.id, Solution.submission_id == sub.id).one_or_none()
        is_mc = False
        mc_filled_counter = 0

        if problem.grading_policy is None:
            problem.grading_policy = GradingPolicy.set_blank
            db.session.commit()

        for mc_option in problem.mc_options:
            box = (mc_option.x, mc_option.y)
            is_mc = True

            if box_is_filled(box, page_img, box_size=CHECKBOX_FORMAT["box_size"]):
                feedback = mc_option.feedback
                sol.feedback.append(feedback)
                mc_filled_counter += 1

                db.session.commit()

        if (mc_filled_counter == 0 and is_mc) or ((not is_mc) and is_blank(problem, page_img, exam.id, sub)):
            set_blank_feedback(problem, sol)

        if problem.grading_policy.value == 2 and mc_filled_counter == 1:
            set_auto_grader(sol)


def set_auto_grader(solution):
    """
    Sets the grader to 'Zesje', meaning that a question is
    considered automatically graded.

    To ensure a solution is graded manually, the grader of a solution
    is set to a grader named Zesje. That way, the detected option is
    not set as 'ungraded'.

    Parameters
    ----------
    solution : Solution
        The solution
    """
    zesje_grader = Grader.query.filter(Grader.name == 'Zesje').one_or_none()

    current_app.logger.info(str(zesje_grader))

    if zesje_grader is None:
        zesje_grader = Grader(name='Zesje')
        db.session.add(zesje_grader)
        db.session.commit()

    solution.graded_by = zesje_grader
    solution.graded_at = datetime.now()
    db.session.commit()


def set_blank_feedback(problem, sol):
    feedback = FeedbackOption.query.filter(FeedbackOption.problem_id == problem.id,
                                           FeedbackOption.text == 'blank').one_or_none()

    if problem.grading_policy.value > 0:
        set_auto_grader(sol)

    if feedback is None:
        new_feedback_option = FeedbackOption(problem_id=problem.id, text='blank')
        db.session.add(new_feedback_option)
        db.session.commit()
        feedback = FeedbackOption.query.filter(FeedbackOption.problem_id == problem.id,
                                               FeedbackOption.text == 'blank').one_or_none()

    sol.feedback.append(feedback)
    db.session.commit()


def is_blank(problem, page_img, exam_id, sub):
    # add the actually margin from the scan to corner markers to the coords in inches
    dpi = guess_dpi(page_img)

    # get the box where we think the box is
    widget_area = np.asarray([
        problem.widget.y,  # top
        problem.widget.y + problem.widget.height,  # bottom
        problem.widget.x,  # left
        problem.widget.x + problem.widget.width,  # right
    ])

    widget_area_in = widget_area / 72

    cut_im = get_box(page_img, widget_area_in, padding=0)

    reference = get_blank(problem, dpi, widget_area_in, exam_id, sub)

    blank_image = np.array(reference)
    blank_image = cv2.cvtColor(blank_image, cv2.COLOR_BGR2GRAY)
    blank_image = np.array(blank_image)
    input_image = np.array(cut_im)
    input_image = cv2.cvtColor(input_image, cv2.COLOR_BGR2GRAY)
    input_image = np.array(input_image)

    n = 0
    max = input_image.shape[0]

    while n + 50 < max:
        m = n + 50
        if (np.average(~input_image[n: m]) > (1.03 * np.average(~blank_image[n: m]))):
            return False
        n = m

    if (np.average(~input_image[n: max-1]) > (1.03 * np.average(~blank_image[n: max-1]))):
        return False

    return True


def get_blank(problem, dpi, widget_area_in, exam_id, sub):
    page = problem.widget.page

    app_config = current_app.config
    data_directory = app_config.get('DATA_DIRECTORY', 'data')
    output_directory = os.path.join(data_directory, f'{exam_id}_data')

    generated_path = os.path.join(output_directory, 'blanks', f'{dpi}')
    if not os.path.exists(generated_path):
        set_blank(sub.copy_number, exam_id, dpi)

    image_path = os.path.join(generated_path, f'page{page:02d}.jpg')
    blank_page = Image.open(image_path)
    box = get_box(np.array(blank_page), widget_area_in, padding=0)
    value = box
    return value


def box_is_filled(box, page_img, threshold=225, cut_padding=0.05, box_size=9):
    """
    A function that finds the checkbox in a general area and then checks if it is filled in.

    Params
    ------
    box: (int, int)
        The coordinates of the top left (x,y) of the checkbox in points.
    page_img: np.array
        A numpy array of the image scan
    threshold: int
        the threshold needed for a checkbox to be considered marked range is between 0 (fully black)
        and 255 (absolutely white).
    cut_padding: float
        The extra padding when retrieving an area where the checkbox is in inches.
    box_size: int
        the size of the checkbox in points.

    Output
    ------
    True if the box is marked, else False.
    """

    # create an array with y top, y bottom, x left and x right. And divide by 72 to get dimensions in inches.
    coords = np.asarray([box[1], box[1] + box_size,
                        box[0], box[0] + box_size])/72

    # add the actually margin from the scan to corner markers to the coords in inches
    dpi = guess_dpi(page_img)

    # get the box where we think the box is
    cut_im = get_box(page_img, coords, padding=cut_padding)

    # convert to grayscale
    gray_im = cv2.cvtColor(cut_im, cv2.COLOR_BGR2GRAY)
    # apply threshold to only have black or white
    _, bin_im = cv2.threshold(gray_im, 160, 255, cv2.THRESH_BINARY)

    h_bin, w_bin, *_ = bin_im.shape
    # create a mask that gets applied when floodfill the white
    mask = np.zeros((h_bin+2, w_bin+2), np.uint8)
    flood_im = bin_im.copy()
    # fill the image from the top left
    cv2.floodFill(flood_im, mask, (0, 0),  0)
    # fill it from the bottom right just in case the top left doesn't cover all the white
    cv2.floodFill(flood_im, mask, (h_bin-2, w_bin-2), 0)

    # find white parts
    coords = cv2.findNonZero(flood_im)
    # Find a bounding box of the white parts
    x, y, w, h = cv2.boundingRect(coords)
    # cut the image to this box
    res_rect = bin_im[y:y+h, x:x+w]

    # the size in pixels we expect the drawn box to
    box_size_px = box_size*dpi / 72

    # if the rectangle is bigger (higher) than expected, cut the image up a bit
    if h > 1.5 * box_size_px:
        y_partition = 0.333
        # try getting another bounding box on bottom 2/3 of the screen
        coords2 = cv2.findNonZero(flood_im[y + int(y_partition * h): y + h, x: x+w])
        x2, y2, w2, h2 = cv2.boundingRect(coords2)
        # add these coords to create a new bounding box we are looking at
        new_y = y+y2 + int(y_partition * h)
        new_x = x + x2
        res_rect = bin_im[new_y:new_y + h2, new_x:new_x + w2]

    else:
        new_x, new_y, w2, h2 = x, y, w, h

    # do the same for width
    if w2 > 1.5 * box_size_px:
        # usually the checkbox is somewhere in the bottom left of the bounding box
        coords3 = cv2.findNonZero(flood_im[new_y: new_y + h2, new_x: new_x + int(0.66 * w2)])
        x3, y3, w3, h3 = cv2.boundingRect(coords3)
        res_rect = bin_im[new_y + y3: new_y + y3 + h3, new_x + x3: new_x + x3 + w3]

    # if the found box is smaller than a certain threshold
    # it means that we only found a little bit of white and the box is filled
    res_x, res_y, *_ = res_rect.shape
    if res_x < 0.333 * box_size_px or res_y < 0.333 * box_size_px:
        return True
    return np.average(res_rect) < threshold
