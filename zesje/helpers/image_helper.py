"""Utilities for dealing with images"""

import numpy as np
import cv2
import math
from wand.color import Color as WandColor
from wand.image import Image as WandImage


def get_widget_image(image_path, widget):
    box = (widget.top, widget.bottom, widget.left, widget.right)
    raw_image = get_box(cv2.imread(image_path), box, padding=0.3)
    return cv2.imencode(".jpg", raw_image)[1].tostring()


def guess_dpi(image_array):
    h, *_ = image_array.shape
    resolutions = np.array([1200, 600, 300, 200, 150,
                            120, 100, 75, 60, 50, 40])
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
    keyp1: OpenCV Keypoint
    keyp2: OpenCV Keypoint

    """
    xdiff = math.fabs(keyp1.pt[0] - keyp2.pt[0])
    ydiff = math.fabs(keyp2.pt[1] - keyp1.pt[1])

    # Avoid division by zero, it is unknown however whether it is turned 90
    # degrees to the left or 90 degrees to the right, therefore we return
    if xdiff == 0:
        return 90

    if keyp1.pt[0] < keyp2.pt[0]:
        if(keyp2.pt[1] > keyp1.pt[1]):
            return -1 * math.degrees(math.atan(ydiff / xdiff))
        else:
            return math.degrees(math.atan(ydiff / xdiff))
    else:
        if(keyp1.pt[1] > keyp2.pt[1]):
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


def check_space_corner(bin_im):
    """Checks if there is enough space to place the corner markers

    Parameters:
    -----------
        bin_im: 2D Array
            The image source in binary

    """
    h, w, *_ = bin_im.shape

    size = math.floor(w/8)
    topleft = np.sum(np.sum(bin_im[0:size, 0:size])) > 0
    topright = np.sum(np.sum(bin_im[0:size, w - size - 1:w - 1])) > 0
    bottomleft = np.sum(np.sum(bin_im[h - size - 1:h - 1, 0:size])) > 0
    bottomright = np.sum(np.sum(
                         bin_im[h - size - 1:h - 1, w - size - 1:w - 1])) > 0

    if topleft or topright or bottomleft or bottomright:
        return False
    else:
        return True


def check_space_idwidget(bin_im):
    # TODO Implement function, since ID widget generation code is still
    # not present
    """Checks if there is enough space to place the identification widget

    Parameters:
    -----------
        bin_im: 2D Array
            The image source in binary

    """

    return False


def check_space_datamatrix(bin_im):
    """Checks if there is enough space to place the data matrix

    Parameters:
    -----------
        bin_im: 2D Array
            The image source in binary

    """
    return False


def check_enough_blankspace(pdf_path):
    """Checks if there is enough space to place all the various widgets

    Parameters:
    -----------
        pdf_path: String
            Path to the pdf file

    """

    result = []

    with WandImage(filename=pdf_path, resolution=150) as pdf:
        for i, page in enumerate(pdf.sequence):
            with WandImage(page) as img:
                img.background_color = WandColor('white')
                img.alpha_channel = 'remove'
                img_buffer = np.asarray(bytearray(
                                        img.make_blob()), dtype=np.uint8)

                if img_buffer is not None:
                    opencv_im = cv2.imdecode(img_buffer, cv2.IMREAD_GRAYSCALE)

                _, bin_im = cv2.threshold(opencv_im,
                                          150, 255, cv2.THRESH_BINARY)

                bin_im = cv2.bitwise_not(bin_im)

                result_id = True

                if (page == 1):
                    result_id = check_space_idwidget(bin_im)
                result_corner = check_space_corner(bin_im)
                result_datam = check_space_datamatrix(bin_im)

                page_result = result_id and result_corner and result_datam
                result.append(page_result)

    return result
