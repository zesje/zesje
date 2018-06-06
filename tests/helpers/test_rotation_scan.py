import pytest
import cv2
import PIL
import os
import math
import numpy as np
from zesje.helpers import image_helper


# Helper functions
# Given 2 keypoints, calculates the distance between them
def distance(keyp1, keyp2):
    return math.hypot(keyp1[0] - keyp2[0], keyp1[1] - keyp2[1])


# Given a name of a exam image and the location it is stored, retrieves the
# image and converts it to binary image
def generate_binary_image(name, datadir):
    pdf_path = os.path.join(datadir, 'scanned_pdfs', f'{name}')
    pil_im = PIL.Image.open(pdf_path)
    opencv_im = cv2.cvtColor(np.array(pil_im), cv2.COLOR_RGB2BGR)
    _, bin_im = cv2.threshold(opencv_im, 150, 255, cv2.THRESH_BINARY)
    return bin_im

# Tests


# Tests whether the output of calc angle is correct
@pytest.mark.parametrize('test_input1, test_input2, expected', [
    ((1337, 69), (9001, 69), 0),
    ((0, 100), (0, 1000), 90),
    ((25, 25), (50, 50), -45),
    ((25, 25), (50, 0), 45)],
    ids=['Same horizontal line', 'Same vertical line', 'Negative angle',
         'Positive angle'])
def test_calc_angle(test_input1, test_input2, expected):
    assert math.isclose(image_helper.calc_angle(test_input1, test_input2),
                        expected, abs_tol=0.1)


# Tests whether the amount of cornermakers is enough to calculate the angle and
# whether it is lower than 5 as we only add 4 corner markers per page.
@pytest.mark.parametrize('name', os.listdir(
                                 os.path.join('tests',
                                              'data', 'scanned_pdfs')),
                         ids=os.listdir(
                            os.path.join('tests', 'data', 'scanned_pdfs')))
def test_detect_enough_cornermarkers(name, datadir):
    bin_im = generate_binary_image(name, datadir)
    keypoints = image_helper.find_corner_marker_keypoints(bin_im)
    assert(len(keypoints) >= 2 & len(keypoints) <= 4)


# Tests whether the detected keypoints are actually corner markers.
# This is done by checking whether they are close enough to the corner
# of the image. Only A4 is considered as there is no test data yet for
# US letter size.
@pytest.mark.parametrize('name', os.listdir(
                                 os.path.join('tests',
                                              'data', 'scanned_pdfs')),
                         ids=os.listdir(
                            os.path.join('tests', 'data', 'scanned_pdfs')))
def test_detect_valid_cornermarkers(name, datadir):
    bin_im = generate_binary_image(name, datadir)
    keypoints = image_helper.find_corner_marker_keypoints(bin_im)

    h, w, *_ = bin_im.shape
    (xmm, ymm) = (210, 297)
    (xcorner, ycorner) = (round(30 * w / xmm), round(30 * h / ymm))
    maxdist = math.hypot(xcorner, ycorner)

    cornerlist = [(0, 0), (0, 0), (0, 0), (0, 0)]

    # Checks whether there aren't multiple keypoints in the same corner.
    # If there is, one of those probably isn't a corner marker.
    result = np.array([0, 0, 0, 0])
    for detected_keypoint in keypoints:
        distlist = np.array([distance(detected_keypoint, corner_keypoint)
                            for corner_keypoint in cornerlist])
        binlist = distlist < maxdist
        result = binlist + result

    assert(sum(result > 1) == 0)


# Untested:
#
# Other parts of the rotation function are not tested due to it being opencv
# functions.
#
