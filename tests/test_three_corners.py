import cv2
import os
import numpy as np

from zesje.images import fix_corner_markers
from zesje.scans import find_corner_marker_keypoints


def test_three_straight_corners_1():
    shape = (240, 200, 3)
    corner_markers = [(50, 50), (120, 50), (50, 200)]

    corner_markers = fix_corner_markers(corner_markers, shape)

    assert (120, 200) in corner_markers


def test_three_straight_corners_2():
    shape = (240, 200, 3)
    corner_markers = [(120, 50), (50, 200), (120, 200)]

    corner_markers = fix_corner_markers(corner_markers, shape)

    assert (50, 50) in corner_markers


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
