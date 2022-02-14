import cv2
import numpy as np
from datetime import datetime

from flask import current_app
from reportlab.lib.units import inch, mm

from .blanks import reference_image
from .database import db, Grader, FeedbackOption, GradingPolicy
from .images import guess_dpi, get_box, widget_area, covers, is_misaligned

mm_per_inch = inch / mm


def grade_problem(copy, page, page_img):
    """
    Automatically checks if a problem is blank, and adds a feedback option
    'blank' if so.
    For multiple choice problems, a feedback option is added for each checkbox
    that is identified as filled in is created.
    For submissions with multipe copies, no grading is done at all.

    Parameters
    ------
    copy : Copy
        the current copy
    page : int
        Page number of the submission
    page_img : np.array
        image of the page
    """
    AUTOGRADER_NAME = current_app.config['AUTOGRADER_NAME']
    sub = copy.submission

    # The solutions to grade are all submissions on the current page that are either
    # not graded yet or graded by Zesje. Submissions with multiple copies are excluded.

    # TODO Support pregrading for submissions with multiple copies.
    solutions_to_grade = [
        sol for sol in sub.solutions
        if (not sol.graded_by or sol.graded_by.oauth_id == AUTOGRADER_NAME) and sol.problem.widget.page == page
    ] if len(sub.copies) == 1 else []

    if solutions_to_grade:
        dpi = guess_dpi(page_img)
        page = solutions_to_grade[0].problem.widget.page
        reference_img = reference_image(sub.exam_id, page, dpi)

    for sol in solutions_to_grade:
        # Completely reset the solution and pregrade with a fresh start
        sol.feedback = []
        sol.grader_id = None
        sol.graded_at = None

        problem = sol.problem

        if not is_problem_misaligned(problem, page_img, reference_img):
            if problem.mc_options:
                grade_mcq(sol, page_img, reference_img)
            elif is_solution_blank(problem, page_img, reference_img):
                grade_as_blank(sol)

    if solutions_to_grade:
        db.session.commit()


def grade_mcq(sol, page_img, reference_img):
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
    reference_img: np.array
        A numpy array of the full page reference image
    """
    problem = sol.problem
    mc_filled_counter = 0

    for mc_option in problem.mc_options:
        box = (mc_option.x, mc_option.y)

        if is_checkbox_filled(box, page_img, reference_img):
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

    BLANK_FEEDBACK_NAME = current_app.config['BLANK_FEEDBACK_NAME']
    feedback = FeedbackOption.query.filter(FeedbackOption.problem_id == sol.problem.id,
                                           FeedbackOption.text == BLANK_FEEDBACK_NAME).first()

    if not feedback:
        feedback = FeedbackOption(problem_id=sol.problem.id, text=BLANK_FEEDBACK_NAME, score=0,
                                  parent=sol.problem.root_feedback)
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
    AUTOGRADER_NAME = current_app.config['AUTOGRADER_NAME']
    zesje_grader = Grader.query.filter(Grader.oauth_id == AUTOGRADER_NAME).one_or_none() or \
        Grader(oauth_id=AUTOGRADER_NAME, name=AUTOGRADER_NAME, internal=True)

    solution.graded_by = zesje_grader
    solution.graded_at = datetime.now()
    db.session.commit()


def is_problem_misaligned(problem, student_img, reference_img):
    """Checks if an image is correctly aligned against the reference

    The check is only executed for the area of the problem.

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
    return is_misaligned(widget_area_in, student_img, reference_img)


def _is_blank(area_inch, page_img, reference_img, padding_inch, binary_threshold, min_area_inch2):
    """Determines if an area of a page is blank

    Params
    ------
    area_inch: numpy array
        An array with consisting of [top, bottom, left, right] in inches
    page_img: np.array
        A numpy array of the full page image scan
    reference_img: np.array
        A numpy array of the full page reference image
    padding_inch: float
        Padding to apply around area_inch, in inch
    binary_threshold: int, between 0 and 255
        The value used to convert grayscale images to binary
    min_area_inch2
        The surface area that is allowed to be filled to still consider it blank

    Returns
    ------
    True if the area is blank, else False
    """
    dpi = guess_dpi(page_img)

    # Extra padding to ensure any content is not cut off
    # in only one of the two images
    padding_pixels = int(padding_inch * dpi)

    # The diameter of the kernel to thicken the lines with. This allows
    # misalignment up to the max alignment error in any direction.
    alignment_error_pixel = current_app.config['MAX_ALIGNMENT_ERROR_MM'] * dpi / mm_per_inch
    kernel_size = 2 * int(alignment_error_pixel) + 1

    min_answer_area_pixels = int(min_area_inch2 * dpi**2)

    student = get_box(page_img, area_inch, padding=padding_inch)
    reference = get_box(reference_img, area_inch, padding=padding_inch)

    return covers(reference, student,
                  padding_pixels=padding_pixels,
                  kernel_size=kernel_size,
                  threshold=min_answer_area_pixels,
                  binary_threshold=binary_threshold)


def is_solution_blank(problem, page_img, reference_img):
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

    padding_inch = 0.2
    min_area_inch2 = current_app.config['MIN_ANSWER_SIZE_MM2'] / (mm_per_inch)**2
    binary_threshold = current_app.config['THRESHOLD_BLANK']

    return _is_blank(
        area_inch=widget_area_in,
        page_img=page_img,
        reference_img=reference_img,
        padding_inch=padding_inch,
        binary_threshold=binary_threshold,
        min_area_inch2=min_area_inch2
    )


def is_checkbox_filled(box_coords,
                       page_img,
                       reference_img):
    """
    Checks whether a checkbox at a specific location is filled

    First, a binary threshold is applied to the input images. Next, template matching
    is applied to find the exact location of the checkbox. Finally the inside of the
    checkbox is checked to be filled for at least a certain threshold.

    Params
    ------
    box_coords: (int, int)
        The coordinates of the top left (x,y) of the checkbox in points.
    page_img: np.array
        A numpy array of the image scan
    reference_img: np.array
        A numpy array of the full page reference image.
        This is currently not used, but might change with an other algorithm.

    Returns
    ------
    True if the box is marked, else False.
    """
    dpi = guess_dpi(page_img)
    box_size = current_app.config['CHECKBOX_SIZE']

    # create an array with y top, y bottom, x left and x right. And divide by 72 to get dimensions in inches.
    coords = np.asarray([box_coords[1], box_coords[1] + box_size,
                        box_coords[0], box_coords[0] + box_size])/72

    min_area_inch2 = current_app.config['MIN_CHECKBOX_SIZE_MM2'] / (mm_per_inch)**2
    binary_threshold = current_app.config['THRESHOLD_MCQ']
    min_answer_area_pixels = int(min_area_inch2 * dpi**2)

    # Extra padding to ensure any content is not cut off due to misalignment
    padding_inch = current_app.config['MAX_ALIGNMENT_ERROR_MM'] / mm_per_inch

    student = get_box(page_img, coords, padding=padding_inch)

    student_gray = cv2.cvtColor(student, cv2.COLOR_BGR2GRAY)
    _, student_bin = cv2.threshold(student_gray, binary_threshold, 255, cv2.THRESH_BINARY)

    # The width of a complete checkbox is its defined width + 1pt line width
    reference_size = int((box_size + 1) / 72 * dpi)
    line_width = int(dpi / 72)

    # A representation of a blank checkbox at this DPI
    reference_bin = np.full((reference_size, reference_size), 255, dtype=np.uint8)
    cv2.rectangle(reference_bin, (0, 0),
                  (reference_bin.shape[0] - 1, reference_bin.shape[1] - 1),
                  0, line_width * 2)

    # The template used for template matching. The same as `reference_bin`, but with the internal area
    # of the checkbox replaced with gray, as we should find marked as well as blank checkboxes.
    template_bin = np.full((reference_size, reference_size), 127, dtype=np.uint8)
    cv2.rectangle(template_bin, (0, 0),
                  (template_bin.shape[0] - 1, template_bin.shape[1] - 1),
                  0, line_width * 2 + 1)

    # Match the template checkbox to the student image. The TM_CCORR method is most
    # sensitive to white areas of the image, so we invert everything to focus on black.
    res = cv2.matchTemplate(~student_bin, ~template_bin, cv2.TM_CCORR)
    *_, max_loc = cv2.minMaxLoc(res)

    # Find the inside of the checkbox on the student image.
    # Crop 1 line width for the line of the checkbox.
    # Crop 1 line width + 1 pixel for small alignment errors.
    x, y = max_loc
    crop = 2 * line_width + 1
    inside_box = student_bin[
        (crop + y):(y + reference_size - crop),
        (crop + x):(x + reference_size - crop)
    ]

    non_covered_pixels = np.count_nonzero(inside_box == 0)

    return non_covered_pixels >= min_answer_area_pixels
