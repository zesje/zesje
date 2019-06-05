import cv2
import numpy as np

from .database import db, Solution
from .images import guess_dpi, get_box, fix_corner_markers


def add_feedback_to_solution(sub, exam, page, page_img, corner_keypoints):
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
    corner_keypoints : array
        locations of the corner keypoints as (x, y) tuples
    """
    problems_on_page = [problem for problem in exam.problems if problem.widget.page == page]

    fixed_corner_keypoints = fix_corner_markers(corner_keypoints, page_img.shape)

    x_min = min(point[0] for point in fixed_corner_keypoints)
    y_min = min(point[1] for point in fixed_corner_keypoints)
    top_left_point = (x_min, y_min)

    for problem in problems_on_page:
        sol = Solution.query.filter(Solution.problem_id == problem.id, Solution.submission_id == sub.id).one_or_none()

        for mc_option in problem.mc_options:
            box = (mc_option.x, mc_option.y)

            if box_is_filled(box, page_img, top_left_point):
                feedback = mc_option.feedback
                sol.feedback.append(feedback)
                db.session.commit()


def box_is_filled(box, page_img, corner_keypoints, marker_margin=72/2.54, threshold=235, cut_padding=0.05, box_size=9):
    """
    A function that finds the checkbox in a general area and then checks if it is filled in.

    Params
    ------
    box: (int, int)
        The coordinates of the top left (x,y) of the checkbox in points.
    page_img: np.array
        A numpy array of the image scan
    corner_keypoints: (float,float)
        The x coordinate of the left markers and the y coordinate of the top markers,
        used as point of reference since scans can deviate from the original.
        (x,y) are both in pixels.
    marker_margin: float
        The margin between the corner markers and the edge of a page when generated.
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

    # shouldn't be needed, but some images are drawn a bit weirdly
    # y_shift = 11
    # create an array with y top, y bottom, x left and x right. use the marker margin to allign to the page.
    coords = np.asarray([box[1], box[1] + box_size,
                        box[0], box[0] + box_size])/72

    # add the actually margin from the scan to corner markers to the coords in inches
    dpi = guess_dpi(page_img)
    # coords[0] = coords[0] + corner_keypoints[1]/dpi
    # coords[1] = coords[1] + corner_keypoints[1]/dpi
    # coords[2] = coords[2] + corner_keypoints[0]/dpi
    # coords[3] = coords[3] + corner_keypoints[0]/dpi

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
        print("in h resize")
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
