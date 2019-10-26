"""Utilities for dealing with images"""

import numpy as np


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


# Modified from https://stackoverflow.com/a/16873755
def blockshaped(arr, block_size):
    """
    Return an array of shape (a * b, block_size, block_size)
    where a and b are the largest possible integers such that
    a * block_size <= arr.shape[0], b * block_size <= arr.shape[1]

    If arr is a 2D array, the returned array looks like n subblocks with
    each subblock preserving the "physical" layout of arr.
    """
    height = (arr.shape[0] // block_size) * block_size
    width = (arr.shape[1] // block_size) * block_size

    cut = arr[:height, :width]

    return (cut.reshape(height//block_size, block_size, -1, block_size)
               .swapaxes(1, 2)
               .reshape(-1, block_size, block_size))
