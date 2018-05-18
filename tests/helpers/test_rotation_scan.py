import pytest
import cv2
import PIL
import os
import math
import numpy as np
from zesje.helpers import image_helper,pdf_helper

# Tests

@pytest.mark.parametrize('test_input1, test_input2, expected', [
    (cv2.KeyPoint(1337,69,0), cv2.KeyPoint(9001,69,0), 0),
    (cv2.KeyPoint(0,100,0), cv2.KeyPoint(0,1000,0), 90),
    (cv2.KeyPoint(25,25,0), cv2.KeyPoint(50,50,0), -45),
    (cv2.KeyPoint(25,25,0), cv2.KeyPoint(50,0,0), 45)],
    ids = ['Same horizontal line', 'Same vertical line', 'Negative angle', 'Positive angle']
)

def test_calc_angle(test_input1, test_input2, expected):
    assert math.isclose(image_helper.calc_angle(test_input1, test_input2), expected, abs_tol=0.1)


@pytest.mark.parametrize('name',
    os.listdir(os.path.join('tests','data','scanned_pdfs')),
    ids = os.listdir(os.path.join('tests','data','scanned_pdfs')))

def test_detect_enough_cornermarkers(name,datadir):
    pdf_path = os.path.join(datadir,'scanned_pdfs', f'{name}')

    pil_im = PIL.Image.open(pdf_path)

    opencv_im = cv2.cvtColor(np.array(pil_im), cv2.COLOR_RGB2BGR)

    _, bin_im = cv2.threshold(opencv_im, 150, 255, cv2.THRESH_BINARY)

    keypoints = image_helper.find_corner_marker_keypoints(bin_im)

    assert(len(keypoints) >= 2 & len(keypoints) <= 4)

# Untested:
#
# Other parts of the rotation function are not tested due to it being opencv
# functions.
