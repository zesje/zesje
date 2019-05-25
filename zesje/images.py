"""Utilities for dealing with images"""

import numpy as np

from operator import sub, add


def guess_dpi(image_array):
    h, *_ = image_array.shape
    resolutions = np.array([1200, 600, 400, 300, 200, 150, 120, 100, 75, 60, 50, 40])
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


def fix_corner_markers(corner_keypoints, shape):
    """
    Corrects the list of corner markers if only three corner markers are found.
    This function raises if less than three corner markers are detected.

    Parameters
    ----------
    corner_keypoints :
        List of corner marker locations as tuples
    shape :
        Shape of the image in (x, y, dim)

    Returns
    -------
    corner_keypoints :
        A list of four corner markers.
    top_left : tuple
        Coordinates of the top left corner marker
    """

    if len(corner_keypoints) == 4 or len(corner_keypoints) < 3:
        raise RuntimeError("Fewer then 3 corner markers found")

    x_sep = shape[1] / 2
    y_sep = shape[0] / 2

    top_left = [(x, y) for x, y in corner_keypoints if x < x_sep and y < y_sep]
    bottom_left = [(x, y) for x, y in corner_keypoints if x < x_sep and y > y_sep]
    top_right = [(x, y) for x, y in corner_keypoints if x > x_sep and y < y_sep]
    bottom_right = [(x, y) for x, y in corner_keypoints if x > x_sep and y > y_sep]

    missing_point = ()

    if not top_left:
        # Top left point is missing
        (dx, dy) = tuple(map(sub, top_right[0], bottom_right[0]))
        missing_point = tuple(map(add, bottom_left[0], (dx, dy)))
        top_left = [missing_point]

    elif not bottom_left:
        # Bottom left point is missing
        (dx, dy) = tuple(map(sub, top_right[0], bottom_right[0]))
        missing_point = tuple(map(sub, top_left[0], (dx, dy)))

    elif not top_right:
        # Top right point is missing
        (dx, dy) = tuple(map(sub, top_left[0], bottom_left[0]))
        missing_point = tuple(map(add, bottom_right[0], (dx, dy)))

    elif not bottom_right:
        # bottom right
        (dx, dy) = tuple(map(sub, top_left[0], bottom_left[0]))
        missing_point = tuple(map(sub, top_right[0], (dx, dy)))

    return top_left[0], corner_keypoints + [missing_point]


def box_is_filled(image_array, box_coords, padding=0.3, threshold=150, pixels=False):
    """
    Determines if a box is filled

    Parameters:
    -----------
    image_array : 2D or 3D array
        The image source.
    box_coords : 4 floats (top, bottom, left, right)
        Coordinates of the bounding box in inches or pixels. By due to differing
        traditions, box coordinates are counted from the bottom left of the
        image, while image array coordinates are from the top left.
    padding : float
        Padding around box borders in inches.
    threshold : int
        Optional threshold value to determine minimal 'darkness'
        to consider a box to be filled in
    pixels : boolean
        Whether the box coordinates are entered as pixels instead of inches.
    """

    # Divide by DPI if pixel coordinates are used
    if pixels:
        box_coords /= guess_dpi(image_array)

    box_img = get_box(image_array, box_coords, padding)

    # Check if the coordinates are outside of the image
    if box_img.size == 0:
        raise RuntimeError("Box coordinates are outside of image")

    avg = np.average(box_img)

    return avg < threshold
