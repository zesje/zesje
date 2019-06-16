"""Utilities for dealing with images"""

import numpy as np


def add_tup(tup1, tup2):
    """
    Adds two tuples

    Parameters
    ----------
    tup1 : tuple
        Tuple 1
    tup2 : tuple
        Tuple 2

    Returns
    -------
    tup : tuple
        The tuple with the sum of the values in tup1 and tup2.
    """
    return tup1[0] + tup2[0], tup1[1] + tup2[1]


def sub_tup(tup1, tup2):
    """Subtracts two tuples

    Parameters
    ----------
    tup1 : tuple
        Tuple 1
    tup2 : tuple
        Tuple 2

    Returns
    -------
    tup : tuple
        The tuple with the difference between the values in tup1 and tup2.
    """
    return tup1[0] - tup2[0], tup1[1] - tup2[1]


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


def get_corner_marker_sides(corner_markers, shape):
    """Divides a list of corner markers in the right sides:

    Parameters
    ----------
    corner_markers : list of tuples
        The list of corner marker points
    shape: tuple
        The shape of an image

    Returns
    -------
    tuples : tuple
        The corner markers divided into sides
    """

    def get_val(tup_list):
        """
        Returns a tuple if present in the list.

        Parameters
        ----------
        tup_list : list of tuples
            List with one tuple

        Returns
        -------
        tup : tuple or None
            Tuple in list or empty list
        """
        return tup_list[0] if tup_list else None

    x_sep = shape[1] / 2
    y_sep = shape[0] / 2

    top_left = get_val([(x, y) for x, y in corner_markers if x < x_sep and y < y_sep])
    top_right = get_val([(x, y) for x, y in corner_markers if x > x_sep and y < y_sep])
    bottom_left = get_val([(x, y) for x, y in corner_markers if x < x_sep and y > y_sep])
    bottom_right = get_val([(x, y) for x, y in corner_markers if x > x_sep and y > y_sep])

    return top_left, top_right, bottom_left, bottom_right


def get_delta(top_left, top_right, bottom_left, bottom_right):
    """Returns the absolute difference between the left or right points

    Parameters
    top_left : tuple
        Top left point
    top_right : tuple
        Top right point
    bottom_left : tuple
        Bottom left point
    bottom_right : tuple
        Bottom right point

    Returns
    -------
    delta : tuple
        The absolute difference as an (x, y) tuple
    """

    if not top_left or not bottom_left:
        return sub_tup(top_right, bottom_right)

    return sub_tup(top_left, bottom_left)


def fix_corner_markers(corner_keypoints, shape):
    """Corrects the list of corner markers if three corner markers are found.
    This function raises if less than three corner markers are found.

    Parameters
    ----------
    corner_keypoints : list of tuples
        List of corner marker locations as tuples
    shape : (float, float, int)
        Shape of the image in (x, y, dim)

    Returns
    -------
    fixed_corners : (float, float)
        A list of four corner markers.
    """
    if len(corner_keypoints) == 4:
        return corner_keypoints

    if len(corner_keypoints) < 3:
        raise RuntimeError("Fewer than 3 corner markers found while trying to fix corners")

    top_left, top_right, bottom_left, bottom_right = get_corner_marker_sides(corner_keypoints, shape)
    delta = get_delta(top_left, top_right, bottom_left, bottom_right)

    if not top_left:
        top_left = add_tup(bottom_left, delta)

    if not top_right:
        top_right = add_tup(bottom_right, delta)

    if not bottom_left:
        bottom_left = sub_tup(top_left, delta)

    if not bottom_right:
        bottom_right = sub_tup(top_right, delta)

    return [top_left, top_right, bottom_left, bottom_right]


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
