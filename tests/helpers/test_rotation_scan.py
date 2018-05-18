import pytest
import cv2
import math
from zesje.helpers import image_helper,pdf_helper

@pytest.mark.parametrize("test_input1, test_input2, expected", [
    (cv2.KeyPoint(0,100,0), cv2.KeyPoint(0,1000,0), 0),
    (cv2.KeyPoint(25,25,0), cv2.KeyPoint(50,50,0), -45),
    (cv2.KeyPoint(25,25,0), cv2.KeyPoint(50,0,0), 45)
])
def test_calc_angle(test_input1, test_input2, expected):
    assert math.isclose(image_helper.calc_angle(test_input1, test_input2), expected, abs_tol=0.1)
