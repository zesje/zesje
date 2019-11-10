import cv2
import numpy as np
from datetime import datetime
from reportlab.lib.units import inch, mm

from .blanks import reference_image
from .database import db, Grader, FeedbackOption, GradingPolicy, Submission, Solution
from .images import guess_dpi, get_box, widget_area
from .pdf_generation import CHECKBOX_FORMAT

AUTOGRADER_NAME = 'Zesje'
BLANK_FEEDBACK_NAME = 'Blank'

# Allow up to 1 mm misalignment in any direction
MAX_ALIGNMENT_ERROR_MM = 1
# Make sure a roughly 1 cm long line written with
# a ballpoint pen is regarded as not blank.
MIN_ANSWER_SIZE_MM2 = 4

mm_per_inch = inch / mm


def grade_problem(sub, page, page_img):
    """
    Automatically checks if a problem is blank, and adds a feedback option
    'blank' if so.
    For multiple choice problems, a feedback option is added for each checkbox
    that is identified as filled in is created.

    Parameters
    ------
    sub : Submission
        the current submission
    page : int
        Page number of the submission
    page_img : np.array
        image of the page
    """
    solutions_to_grade = [
        sol for sol in sub.solutions
        if (not sol.graded_by or sol.graded_by.name == AUTOGRADER_NAME) and sol.problem.widget.page == page
    ]

    if solutions_to_grade:
        dpi = guess_dpi(page_img)
        page = solutions_to_grade[0].problem.widget.page
        reference_img = reference_image(sub.exam_id, page, dpi)

    for sol in solutions_to_grade:
        sol.feedback = []
        problem = sol.problem

        if not is_misaligned(problem, page_img, reference_img):
            if problem.mc_options:
                grade_mcq(sol, page_img)
            elif is_blank(problem, page_img, reference_img):
                grade_as_blank(sol)

    db.session.commit()


def grade_mcq(sol, page_img):
    """
    Pre-grades a multiple choice problem.
    This function does either of two things:
    - Adds a feedback option 'blank' if no option has been detected as filled
    - Adds a feedback option for every option that has been detected as filled

    In both cases, a grader named 'Zesje' is set for this problem.

    Parameters
    ----------
    sol : Solution
        The solution to the multiple choice question
    page_img: np.array
        A numpy array of the image scan
    """
    box_size = CHECKBOX_FORMAT["box_size"]
    problem = sol.problem
    mc_filled_counter = 0

    for mc_option in problem.mc_options:
        box = (mc_option.x, mc_option.y)

        if box_is_filled(box, page_img, box_size=box_size):
            feedback = mc_option.feedback
            sol.feedback.append(feedback)
            mc_filled_counter += 1

    if mc_filled_counter == 0:
        grade_as_blank(sol)
    elif mc_filled_counter == 1 and problem.grading_policy == GradingPolicy.set_single:
        set_auto_grader(sol)

    db.session.commit()


def grade_as_blank(sol):
    """
    Pre-grades a solution as identified as blank.

    Parameters
    ----------
    sol : Solution
        The solution to pre-grade
    """
    if sol.problem.grading_policy == GradingPolicy.set_blank:
        set_auto_grader(sol)

    feedback = FeedbackOption.query.filter(FeedbackOption.problem_id == sol.problem.id,
                                           FeedbackOption.text == BLANK_FEEDBACK_NAME).first()

    if not feedback:
        feedback = FeedbackOption(problem_id=sol.problem.id, text=BLANK_FEEDBACK_NAME, score=0)
        db.session.add(feedback)

    sol.feedback.append(feedback)
    db.session.commit()


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
    zesje_grader = Grader.query.filter(Grader.name == AUTOGRADER_NAME).one_or_none() or Grader(name=AUTOGRADER_NAME)

    solution.graded_by = zesje_grader
    solution.graded_at = datetime.now()
    db.session.commit()


def is_misaligned(problem, student_img, reference_img):
    """Checks if an image is correctly aligned against the reference

    This is done by thickening the lines in the student image and
    checking if this thickened image fully covers the reference image.

    Params
    ------
    problem: Problem
        An instance of the problem to be checked
    page_img: np.array
        A numpy array of the full page image scan
    reference_img: np.array
        A numpy array of the full page reference image
    """
    widget_area_in = widget_area(problem)
    dpi = guess_dpi(student_img)

    # Extra padding to ensure any content is not cut off
    # in only one of the two images
    padding_inch = 0.2
    padding_pixels = int(padding_inch * dpi)

    # The diameter of the kernel to thicken the lines with. This allows
    # misalignment up to the max alignment error in any direction.
    kernel_size_mm = 2 * MAX_ALIGNMENT_ERROR_MM
    kernel_size = int(kernel_size_mm * dpi / mm_per_inch)

    student = get_box(student_img, widget_area_in, padding=padding_inch)
    reference = get_box(reference_img, widget_area_in, padding=padding_inch)

    return not covers(student, reference,
                      padding_pixels=padding_pixels,
                      kernel_size=kernel_size)


def is_blank(problem, page_img, reference_img):
    """Determines if a solution is blank

    Params
    ------
    problem: Problem
        An instance of the problem to be checked
    page_img: np.array
        A numpy array of the full page image scan
    reference_img: np.array
        A numpy array of the full page reference image

    Returns
    ------
    True if the solution is blank, else False
    """
    widget_area_in = widget_area(problem)
    dpi = guess_dpi(page_img)

    # Extra padding to ensure any content is not cut off
    # in only one of the two images
    padding_inch = 0.2
    padding_pixels = int(padding_inch * dpi)

    # The diameter of the kernel to thicken the lines with. This allows
    # misalignment up to the max alignment error in any direction.
    kernel_size_mm = 2 * MAX_ALIGNMENT_ERROR_MM
    kernel_size = int(kernel_size_mm * dpi / mm_per_inch)

    min_answer_area_pixels = int(MIN_ANSWER_SIZE_MM2 * dpi**2 / (mm_per_inch)**2)

    student = get_box(page_img, widget_area_in, padding=padding_inch)
    reference = get_box(reference_img, widget_area_in, padding=padding_inch)

    return covers(reference, student,
                  padding_pixels=padding_pixels,
                  kernel_size=kernel_size,
                  threshold=min_answer_area_pixels)


def covers(cover_img, to_cover_img, padding_pixels=0, threshold=0, kernel_size=9):
    """Check if an image covers another image

    First, both images are converted to binary. Then, all the content
    in `cover_img` is dilated. Finally it checks if the dilated cover
    image covers `to_cover_img` up to a threshold in pixels.

    This function handles white as open space, black as filled space.

    Params
    ------
    cover_img: np.array
        The image that is used as cover
    to_cover_img: np.array
        The image that is going to be covered
    padding_pixels: int
        The amount of padding to remove before checking if it is covered
    threshold: int
        The amount of pixels that are allowed to not be covered
    kernel_size: int
        The diameter in pixels of the kernel that is used to thicken the lines
    """
    cover = cv2.cvtColor(cover_img, cv2.COLOR_BGR2GRAY)
    _, cover_bin = cv2.threshold(cover, 150, 255, cv2.THRESH_BINARY)

    to_cover = cv2.cvtColor(to_cover_img, cv2.COLOR_BGR2GRAY)
    _, to_cover_bin = cv2.threshold(to_cover, 150, 255, cv2.THRESH_BINARY)

    kernel = np.ones((kernel_size, kernel_size), dtype=np.uint8)
    cover_thick = cv2.erode(cover_bin, kernel, iterations=1)

    difference = ~(cover_thick - to_cover_bin)[padding_pixels:-padding_pixels, padding_pixels:-padding_pixels]

    non_covered_pixels = np.count_nonzero(difference == 0)

    return non_covered_pixels <= threshold


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

    Returns
    ------
    True if the box is marked, else False.
    """

    # create an array with y top, y bottom, x left and x right. And divide by 72 to get dimensions in inches.
    coords = np.asarray([box[1], box[1] + box_size,
                        box[0], box[0] + box_size])/72

    dpi = guess_dpi(page_img)

    cut_im = get_box(page_img, coords, padding=cut_padding)

    gray_im = cv2.cvtColor(cut_im, cv2.COLOR_BGR2GRAY)
    _, bin_im = cv2.threshold(gray_im, 160, 255, cv2.THRESH_BINARY)

    h_bin, w_bin, *_ = bin_im.shape
    mask = np.zeros((h_bin+2, w_bin+2), np.uint8)
    flood_im = bin_im.copy()
    cv2.floodFill(flood_im, mask, (0, 0),  0)
    # fill it from the bottom right just in case the top left doesn't cover all the white
    cv2.floodFill(flood_im, mask, (h_bin-2, w_bin-2), 0)

    coords = cv2.findNonZero(flood_im)
    x, y, w, h = cv2.boundingRect(coords)
    res_rect = bin_im[y:y+h, x:x+w]

    box_size_px = box_size * dpi / 72

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
        # usually the checkbox is somewhere in the bottom left of the bounding box after applying the previous steps
        coords3 = cv2.findNonZero(flood_im[new_y: new_y + h2, new_x: new_x + int(0.66 * w2)])
        x3, y3, w3, h3 = cv2.boundingRect(coords3)
        res_rect = bin_im[new_y + y3: new_y + y3 + h3, new_x + x3: new_x + x3 + w3]

    # if the found box is smaller than a certain threshold
    # it means that we only found a little bit of white and the box is filled
    res_x, res_y, *_ = res_rect.shape
    if res_x < 0.333 * box_size_px or res_y < 0.333 * box_size_px:
        return True
    return np.average(res_rect) < threshold


def ungrade_multiple_sub(student_id, exam_id, commit=True):
    """
    Ungrade all solutions of a specific student if they have more than one submission.

    This function does not remove the selected feedback options, but sets the
    graded_at and grader_id fields to None such that it has to be approved again.

    Params
    ------
    student_id: int
        The student number of the student to check
    exam_id: int
        The exam to perform the check on
    """
    submission_ids = [sub.id for sub in Submission.query.filter(Submission.student_id == student_id,
                                                                Submission.exam_id == exam_id).all()]
    if len(submission_ids) > 1:
        Solution.query \
                .filter(Solution.submission_id.in_(submission_ids)) \
                .update({Solution.grader_id: None, Solution.graded_at: None},
                        synchronize_session='fetch')

        if commit:
            db.session.commit()
