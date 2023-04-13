import math
import os

import numpy as np
import PIL
import pytest

from zesje import scans


# Helper functions
# Given 2 keypoints, calculates the distance between them
def distance(keyp1, keyp2):
    return math.hypot(keyp1[0] - keyp2[0], keyp1[1] - keyp2[1])


# Given a name of a exam image and the location it is stored, retrieves the
# image and converts it to binary image
def generate_image(name, datadir):
    pdf_path = os.path.join(datadir, "scanned_pdfs", f"{name}")
    pil_im = PIL.Image.open(pdf_path)
    pil_im = pil_im.convert("RGB")
    image_array = np.array(pil_im)
    return image_array


# Tests


# Tests whether the output of calc angle is correct
@pytest.mark.parametrize(
    "test_input1, test_input2, expected",
    [((1337, 69), (9001, 69), 0), ((0, 100), (0, 1000), 90), ((25, 25), (50, 50), -45), ((25, 25), (50, 0), 45)],
    ids=["Same horizontal line", "Same vertical line", "Negative angle", "Positive angle"],
)
def test_calc_angle(test_input1, test_input2, expected):
    assert math.isclose(scans.calc_angle(test_input1, test_input2), expected, abs_tol=0.1)


# Tests whether the amount of cornermakers is enough to calculate the angle and
# whether it is lower than 5 as we only add 4 corner markers per page.
test_args = [
    ("blank.jpg", 0),
    ("missing_two_corners.jpg", 2),
    ("sample_exam.jpg", 4),
    ("shifted.jpg", 4),
    ("tilted.jpg", 4),
    ("tilted_extreme.jpg", 4),
    ("tilted_extreme_2.jpg", 4),
    ("messy_three_corners.jpg", 3),
]


@pytest.mark.parametrize("name,expected", test_args, ids=list(map(lambda e: f"{e[0]} ({e[1]} markers)", test_args)))
def test_detect_enough_cornermarkers(name, expected, datadir, config_app):
    image = generate_image(name, datadir)
    keypoints = scans.find_corner_marker_keypoints(image)
    assert len(keypoints) == expected


# Tests whether the detected keypoints are actually corner markers.
# This is done by checking whether they are close enough to the corner
# of the image. Only A4 is considered as there is no test data yet for
# US letter size.
@pytest.mark.parametrize("name", map(lambda tup: tup[0], test_args))
def test_detect_valid_cornermarkers(name, datadir, config_app):
    image = generate_image(name, datadir)
    keypoints = scans.find_corner_marker_keypoints(image)

    h, w, *_ = image.shape
    (xmm, ymm) = (210, 297)
    (xcorner, ycorner) = (round(30 * w / xmm), round(30 * h / ymm))
    maxdist = math.hypot(xcorner, ycorner)

    cornerlist = [(0, 0), (0, 0), (0, 0), (0, 0)]

    # Checks whether there aren't multiple keypoints in the same corner.
    # If there is, one of those probably isn't a corner marker.
    result = np.array([0, 0, 0, 0])
    for detected_keypoint in keypoints:
        distlist = np.array([distance(detected_keypoint, corner_keypoint) for corner_keypoint in cornerlist])
        binlist = distlist < maxdist
        result = binlist + result

    assert sum(result > 1) == 0


# Untested:
#
# Other parts of the rotation function are not tested due to it being opencv
# functions.
#
