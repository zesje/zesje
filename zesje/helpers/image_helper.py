"""Utilities for dealing with images"""

import numpy as np
import cv2
import math

def get_widget_image(image_path, widget):
    box = (widget.top, widget.bottom, widget.left, widget.right)
    raw_image = get_box(cv2.imread(image_path), box, padding=0.3)
    return cv2.imencode(".jpg", raw_image)[1].tostring()


def guess_dpi(image_array):
    h, *_ = image_array.shape
    resolutions = np.array([1200, 600, 300, 200, 150, 120, 100, 75, 60, 50, 40])
    return resolutions[np.argmin(abs(resolutions - 25.4 * h / 297))]


def get_box(image_array, box, padding):
    """Extract a subblock from an array corresponding to a scanned A4 page.

    Parameters:
    -----------
    image_array : 2D or 3D array
        The image source.
    box : 4 floats (top, bottom, left, right)
        Coordinates of the bounding box in inches. By due to differing
        traditions, box coordinates are counted from the bottom left of the
        image, while image array coordinates are from the top left.
    padding : float
        Padding around box borders in inches.
    """
    h, w, *_ = image_array.shape
    dpi = guess_dpi(image_array)
    box = np.array(box)
    box += (padding, -padding, -padding, padding)
    box = (np.array(box) * dpi).astype(int)
    # Here we are not returning the lowest pixel of the image because otherwise
    # the numpy slicing is not correct.
    top, bottom = min(h, box[0]), max(1, box[1])
    left, right = max(0, box[2]), min(w, box[3])
    return image_array[-top:-bottom, left:right]


def calc_angle(keyp1, keyp2):
    """Calculates the angle of the line connecting two keypoints in an image
    Calculates it with respect to the horizontal axis.

    Parameters:
    -----------
    keyp1: Tuple in the form of (x,y) with origin top left
    keyp2: Tuple in the form of (x,y) with origin top left

    """
    xdiff = math.fabs(keyp1[0] - keyp2[0])
    ydiff = math.fabs(keyp2[1] - keyp1[1])

    # Avoid division by zero, it is unknown however whether it is turned 90
    # degrees to the left or 90 degrees to the right, therefore we return
    if xdiff == 0:
        return 90

    if keyp1[0] < keyp2[0]:
        if(keyp2[1] > keyp1[1]):
            return -1 * math.degrees(math.atan(ydiff / xdiff))
        else:
            return math.degrees(math.atan(ydiff / xdiff))
    else:
        if(keyp1[1] > keyp2[1]):
            return -1 * math.degrees(math.atan(ydiff / xdiff))
        else:
            return math.degrees(math.atan(ydiff / xdiff))


def find_corner_marker_keypoints(bin_im):
    """Generates a list of OpenCV keypoints which resemble corner markers.
    This is done using a SimpleBlobDetector

    Parameters:
    -----------
    bin_im: OpenCV binary image

    """

    # Filter out everything in the center of the image
    h, w, *_ = bin_im.shape
    bin_im[round(0.125 * h):round(0.875 * h),
           round(0.125 * w):round(0.875 * w)] = 1

    # Detect objects which look like corner markers
    params = cv2.SimpleBlobDetector_Params()
    params.filterByArea = True
    params.minArea = 150
    params.maxArea = 400
    params.filterByCircularity = True
    params.minCircularity = 0
    params.maxCircularity = 0.15
    params.filterByConvexity = True
    params.minConvexity = 0.15
    params.maxConvexity = 0.3
    params.filterByInertia = True
    params.minInertiaRatio = 0.20
    params.maxInertiaRatio = 0.50
    params.filterByColor = False

    detector = cv2.SimpleBlobDetector_create(params)
    return detector.detect(bin_im)
