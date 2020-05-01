"""Utilities for dealing with images"""

import numpy as np
import cv2

from reportlab.lib.units import inch, mm
from flask import current_app

mm_per_inch = inch / mm


def guess_dpi(image_array):
    h, *_ = image_array.shape
    resolutions = np.array([1200, 600, 400, 300, 200, 150, 144, 120, 100, 75, 72, 60, 50, 40])
    return resolutions[np.argmin(abs(resolutions - 25.4 * h / 297))]


def get_box(image_array, box, padding=0.3):
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
    # TODO: use points as base unit
    h, w, *_ = image_array.shape
    dpi = guess_dpi(image_array)
    box = np.array(box)
    box += (-padding, padding, -padding, padding)
    box = (np.array(box) * dpi).astype(int)
    # Here we are not returning the lowest pixel of the image because otherwise
    # the numpy slicing is not correct.
    top, bottom = max(0, min(box[0], h)), max(1, min(box[1], h))
    left, right = max(0, min(box[2], w)), max(1, min(box[3], w))
    return image_array[top:bottom, left:right]


def widget_area(problem):
    """Get the coordinates of the widget area of a problem in inches

    Parameters
    ----------
    problem: Problem
        An instance of the problem to get the widget area for

    Returns
    ------
    widget_area_in : numpy array
        An array with consisting of [top, bottom, left, right] in inches
    """
    widget_area = np.asarray([
        problem.widget.y,  # top
        problem.widget.y + problem.widget.height,  # bottom
        problem.widget.x,  # left
        problem.widget.x + problem.widget.width,  # right
    ])

    widget_area_in = widget_area / 72

    return widget_area_in


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


def is_misaligned(area_inch, img, reference, padding_inch=0.2):
    """Checks if an image is correctly aligned against the reference

    The check is only executed for the supplied area.

    This is done by thickening the lines in the student image and
    checking if this thickened image fully covers the reference image.

    Params
    ------
    area_inch: numpy array
        An array with consisting of [top, bottom, left, right] in inches
    img: np.array
        A numpy array of the full page image scan
    reference: np.array
        A numpy array of the full page reference image
    padding_inch: float
        Extra padding to apply such that content is not cut off, in inches
    """
    dpi = guess_dpi(img)
    padding_pixels = int(padding_inch * dpi)

    # The diameter of the kernel to thicken the lines with. This allows
    # misalignment up to the max alignment error in any direction.
    kernel_size_mm = 2 * current_app.config['MAX_ALIGNMENT_ERROR_MM']
    kernel_size = int(kernel_size_mm * dpi / mm_per_inch)

    img_cropped = get_box(img, area_inch, padding=padding_inch)
    reference_cropped = get_box(reference, area_inch, padding=padding_inch)

    return not covers(img_cropped, reference_cropped,
                      padding_pixels=padding_pixels,
                      kernel_size=kernel_size)
