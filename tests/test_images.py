import cv2
import os
import numpy as np
import pytest

from zesje.images import get_delta, get_corner_marker_sides, fix_corner_markers, add_tup, sub_tup
from zesje.scans import find_corner_marker_keypoints


@pytest.mark.parametrize(
    'shape,corners,expected',
    [((240, 200, 3), [(50, 50), (120, 50), (50, 200)], (120, 200)),
        ((240, 200, 3), [(120, 50), (50, 200), (120, 200)], (50, 50))],
    ids=["", ""])
def test_three_straight_corners(shape, corners, expected):
    corner_markers = fix_corner_markers(corners, shape)
    assert expected in corner_markers


def test_pdf(datadir):
    # Max deviation of inferred corner marker and actual location
    epsilon = 2

    # Scan rotated image with 4 corner markers
    image_filename1 = 'a4-rotated.png'
    image_path = os.path.join(datadir, 'cornermarkers', image_filename1)
    page_img = cv2.imread(image_path)

    corners1 = find_corner_marker_keypoints(page_img)

    # Scan the same image with 3 corner markers
    image_filename2 = 'a4-rotated-3-markers.png'
    image_path = os.path.join(datadir, 'cornermarkers', image_filename2)
    page_img = cv2.imread(image_path)

    corners2 = find_corner_marker_keypoints(page_img)

    # Get marker that was removed
    diff = [corner for corner in corners1 if corner not in corners2]
    diff_marker = min(diff)

    fixed_corners2 = fix_corner_markers(corners2, page_img.shape)
    added_marker = [corner for corner in fixed_corners2 if corner not in corners1][0]

    # Check if 'inferred' corner marker is not too far away
    dist = np.linalg.norm(np.subtract(added_marker, diff_marker))

    assert dist < epsilon


def test_get_delta_1():
    delta = get_delta((0, 1), (1, 1), (0, 0), None)

    assert delta == (0, 1)


def test_get_delta_2():
    delta = get_delta((0, 1), None, (0, 0), (0, 1))

    assert delta == (0, 1)


def test_get_corner_marker_sides_all_four():
    shape = (100, 100)
    corner_markers = [(0, 0), (100, 0), (0, 100), (100, 100)]

    assert tuple(corner_markers) == get_corner_marker_sides(corner_markers, shape)


def test_get_corner_markers_three():
    shape = (100, 100)
    corner_markers = [(0, 0), (0, 100), (100, 0)]

    top_left, top_right, bottom_left, bottom_right = get_corner_marker_sides(corner_markers, shape)

    assert not bottom_right


def test_add_tup():
    tup1 = tup2 = (1, 1)

    assert add_tup(tup1, tup2) == (2, 2)


def test_sub_tup():
    tup1 = tup2 = (1, 1)

    assert sub_tup(tup1, tup2) == (0, 0)
