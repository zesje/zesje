"""Utilities for dealing with images"""

import numpy as np
import cv2
import math

def get_widget_image(image_path, widget):
    box = (widget.top, widget.bottom, widget.left, widget.right)
    raw_image = get_box(cv2.imread(image_path), box, padding=0.3)
    return cv2.imencode(".jpg", raw_image)[1].tostring()


def guess_dpi(image_array):
    h, *_ = image_array.shape
    resolutions = np.array([1200, 600, 300, 200, 150, 120, 100, 75, 60, 50, 40])
    return resolutions[np.argmin(abs(resolutions - 25.4 * h / 297))]


def get_box(image_array, box, padding):
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
    h, w, *_ = image_array.shape
    dpi = guess_dpi(image_array)
    box = np.array(box)
    box += (padding, -padding, -padding, padding)
    box = (np.array(box) * dpi).astype(int)
    # Here we are not returning the lowest pixel of the image because otherwise
    # the numpy slicing is not correct.
    top, bottom = min(h, box[0]), max(1, box[1])
    left, right = max(0, box[2]), min(w, box[3])
    return image_array[-top:-bottom, left:right]


def calc_angle(keyp1, keyp2):
    """Calculates the angle of the line connecting two keypoints in an image
    Calculates it with respect to the horizontal axis.

    Parameters:
    -----------
    keyp1: Keypoint represented by a tuple in the form of (x,y) with
    origin top left
    keyp2: Keypoint represented by a tuple in the form of (x,y) with
    origin top left

    """
    xdiff = math.fabs(keyp1[0] - keyp2[0])
    ydiff = math.fabs(keyp2[1] - keyp1[1])

    # Avoid division by zero, it is unknown however whether it is turned 90
    # degrees to the left or 90 degrees to the right, therefore we return
    if xdiff == 0:
        return 90

    if keyp1[0] < keyp2[0]:
        if(keyp2[1] > keyp1[1]):
            return -1 * math.degrees(math.atan(ydiff / xdiff))
        else:
            return math.degrees(math.atan(ydiff / xdiff))
    else:
        if(keyp1[1] > keyp2[1]):
            return -1 * math.degrees(math.atan(ydiff / xdiff))
        else:
            return math.degrees(math.atan(ydiff / xdiff))


def find_corner_marker_keypoints(image_data):
    """Generates a list of OpenCV keypoints which resemble corner markers.
    This is done using a SimpleBlobDetector

    Parameters:
    -----------
    image_data: Source image

    """
    color_im = cv2.cvtColor(np.array(image_data), cv2.COLOR_RGB2BGR)
    gray_im = cv2.cvtColor(color_im, cv2.COLOR_BGR2GRAY)
    _, bin_im = cv2.threshold(gray_im, 150, 255, cv2.THRESH_BINARY)

    h, w, *_ = color_im.shape

    bin_im_inv = cv2.bitwise_not(bin_im)

    im_floodfill = bin_im_inv.copy()

    # Mask used for flood filling.
    # Notice the size needs to be 2 pixels larger than the image for floodFill
    # to function.
    mask = np.zeros((h+2, w+2), np.uint8)

    # Floodfill from point (0, 0)
    cv2.floodFill(im_floodfill, mask, (0, 0), 255)

    im_floodfill_inv = cv2.bitwise_not(im_floodfill)

    # Combine the two images to get the original image but with all enclosed
    # space completely black.
    bin_im = ~(bin_im_inv | im_floodfill_inv)

    # Filter out everything in the center of the image
    bin_im[round(0.125 * h):round(0.875 * h),
           round(0.125 * w):round(0.875 * w)] = 255

    # Detect objects which look like corner markers
    params = cv2.SimpleBlobDetector_Params()
    params.filterByArea = True
    params.minArea = 150
    params.maxArea = 1500
    params.filterByCircularity = True
    params.minCircularity = 0
    params.maxCircularity = 0.15
    params.filterByConvexity = True
    params.minConvexity = 0.15
    params.maxConvexity = 0.3
    params.filterByInertia = True
    params.minInertiaRatio = 0.20
    params.maxInertiaRatio = 0.50
    params.filterByColor = False

    detector = cv2.SimpleBlobDetector_create(params)
    blob_keypoints = detector.detect(bin_im)

    corner_keypoints = []

    # For each blob keypoint, extract an image patch as a descriptor
    for keyp in blob_keypoints:
        pt_x, pt_y = keyp.pt[0], keyp.pt[1]
        topleft = (int(round(pt_x - 0.75 * keyp.size)),
                   int(round(pt_y - 0.75 * keyp.size)))
        bottomright = (int(round(pt_x + 0.75 * keyp.size)),
                       int(round(pt_y + 0.75 * keyp.size)))
        image_patch = gray_im[topleft[1]:bottomright[1],
                              topleft[0]:bottomright[0]]

        # Find the best corner
        corners = cv2.goodFeaturesToTrack(image_patch, 1, 0.01, 10)
        corners = np.int0(corners)

        # Change the coordinates of the corner to be respective of the origin
        # of the original image, and not the image patch.
        patch_x, patch_y = corners.ravel()
        corner_x, corner_y = patch_x + topleft[0], patch_y + topleft[1]

        corner_keypoints.append((corner_x, corner_y))

    return corner_keypoints


def check_corner_keypoints(image_array, keypoints):
    """Checks whether the corner markers are valid.
        1. Checks whether there is 3 or more corner markers
        2. Checks whether there exist no 2 corner markers
           in the same corner of the image.

    Parameters:
    -----------
    image_array: source image
    keypoints: list of tuples containing the coordinates of keypoints
    """
    if(len(keypoints) < 3 or len(keypoints) > 4):
        raise RuntimeError('Incorrect amount of corner markers detected')

    h, w, *_ = image_array.shape

    checklist = [False, False, False, False]

    for (x, y) in keypoints:opencv_im = cv2.imread(path_to_image,cv2.IMREAD_COLOR)
    opencv_im_copy = opencv_im.copy()
    gray_im = cv2.cvtColor(opencv_im,cv2.COLOR_BGR2GRAY)

    _, bin_im = cv2.threshold(gray_im, 150, 255, cv2.THRESH_BINARY)

    #Filter out everything in the center of the image
    h, w, *_ = bin_im.shape
    bin_im[round(0.125*h):round(0.875*h),round(0.125*w):round(0.875*w)] = 1

    #Detect objects which look like corner markers
    params = cv2.SimpleBlobDetector_Params()
    params.filterByArea = True
    params.minArea = 1000
    params.maxArea = 2000
    params.filterByCircularity = True
    params.minCircularity = 0
    params.maxCircucorner_keypointslarity = 0.1
    params.filterByConvexity = True
    params.minConvexity = 0.2
    params.maxConvexity = 0.8
    params.filterByInertia = True
    params.minInertiaRatio = 0
    params.maxInertiaRatio = 0.5
    params.filterByColor = False
            is_left_half = 2 * int(x < (w / 2))
            is_top_half = 1 * int(y < (h / 2))
            index = is_left_half + is_top_half
            if(checklist[index]):
                raise RuntimeError(("Found multiple corner markers"
                                    "in the same corner"))
            else:
                checklist[index] = True


def find_orientation_bar(image_array):

    color_im = cv2.cvtColor(np.array(image_data), cv2.COLOR_RGB2BGR)
    opencv_im_copy = opencv_im.copy()
    gray_im = cv2.cvtColor(opencv_im, cv2.COLOR_BGR2GRAY)

    _, bin_im = cv2.threshold(gray_im, 150, 255, cv2.THRESH_BINARY)

    # Filter out everything in the center of the image
    h, w, *_ = bin_im.shape
    bin_im[round(0.125*h):round(0.875*h), round(0.125*w):round(0.875*w)] = 1

    # Detect objects which look like corner markers
    params = cv2.SimpleBlobDetector_Params()
    params.filterByArea = True
    params.minArea = 1000
    params.maxArea = 2000
    params.filterByCircularity = True
    params.minCircularity = 0
    params.maxCircularity = 0.1
    params.filterByConvexity = True
    params.minConvexity = 0.2
    params.maxConvexity = 0.8
    params.filterByInertia = True
    params.minInertiaRatio = 0
    params.maxInertiaRatio = 0.5
    params.filterByColor = False

    detector = cv2.SimpleBlobDetector_create(params)
    keypoints = detector.detect(bin_im)

    bar_keypoints = [(keyp.pt[0], keyp.pt[1]) for keyp in keypoints]

    return bar_keypoints
