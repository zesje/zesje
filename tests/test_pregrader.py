import os
import pytest
from PIL import Image
import numpy as np
from zesje import pregrader
from zesje import scans
from zesje import images

directory_name = "checkboxes"


@pytest.fixture
def scanned_image(datadir):
    image_filename = os.path.join(datadir, directory_name, "scanned_page.jpg")
    image = Image.open(image_filename)
    image = np.array(image)
    return image


@pytest.fixture
def scanned_image_keypoints(scanned_image):
    corner_markers = scans.find_corner_marker_keypoints(scanned_image)
    fixed_corner_keypoints = images.fix_corner_markers(corner_markers, scanned_image.shape)
    return fixed_corner_keypoints


@pytest.mark.parametrize('box_coords, result', [((346, 479), True), ((370, 479), False), ((393, 479), True),
                                                ((416, 479), True), ((439, 479), True), ((155, 562), True)],)
def test_ideal_crops(datadir, box_coords, result, scanned_image_keypoints, scanned_image):
    assert pregrader.box_is_filled(box_coords, scanned_image, scanned_image_keypoints[0]) == result


@pytest.mark.parametrize('box_coords, result', [((341, 471), True), ((352, 482), True), ((448, 482), True),
                                                ((423, 474), True), ((460, 475), False), ((477, 474), True)],
                         ids=["1 filled bottom right", "1 filled top left", "5 filled with a bit of 6",
                              "4 fully filled with the label", "6 empty with label",
                              "7 partially  cropped, filled and a part of 6"])
def test_shifted_crops(datadir, box_coords, result, scanned_image_keypoints, scanned_image):
    assert pregrader.box_is_filled(box_coords, scanned_image, scanned_image_keypoints[0]) == result
