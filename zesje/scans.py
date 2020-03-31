import functools
import itertools
import math
import os
from collections import namedtuple
import signal

import cv2
import numpy as np
from scipy import spatial
from flask import current_app

from PIL import Image
from pikepdf import Pdf
from pylibdmtx import pylibdmtx
from sqlalchemy.exc import InternalError

from .database import db, Scan, Exam, Page, Student, Submission, Solution, ExamWidget
from .datamatrix import decode_raw_datamatrix
from .images import guess_dpi, get_box
from .pregrader import grade_problem, ungrade_multiple_sub
from .image_extraction import extract_images
from .blanks import reference_image
from . import celery

ExtractedBarcode = namedtuple('ExtractedBarcode', ['token', 'copy', 'page'])

ExamMetadata = namedtuple('ExamMetadata', ['token', 'barcode_coords'])


@celery.task()
def process_pdf(scan_id):
    """Process a PDF, recording progress to a database

    Parameters
    ----------
    scan_id : int
        The ID in the database of the Scan to process
    """

    def raise_exit(signo, frame):
        raise SystemExit('PDF processing was killed by an external signal')

    # We want to trigger an exit from within Python when a signal is received.
    # The default behaviour for SIGTERM is to terminate the process without
    # calling 'atexit' handlers, and SIGINT raises keyboard interrupt.
    for signal_type in (signal.SIGINT, signal.SIGTERM):
        signal.signal(signal_type, raise_exit)

    try:
        _process_pdf(scan_id)
    except BaseException as error:
        # TODO: When #182 is implemented, properly separate user-facing
        #       messages (written to DB) from developer-facing messages,
        #       which should be written into the log.
        write_pdf_status(scan_id, 'error', "Unexpected error: " + str(error))


def _process_pdf(scan_id):
    data_directory = current_app.config['DATA_DIRECTORY']

    report_error = functools.partial(write_pdf_status, scan_id, 'error')
    report_progress = functools.partial(write_pdf_status, scan_id, 'processing')
    report_success = functools.partial(write_pdf_status, scan_id, 'success')

    # Raises exception if zero or more than one scans found
    scan = Scan.query.filter(Scan.id == scan_id).one()

    report_progress('Importing PDF')

    pdf_path = os.path.join(data_directory, 'scans', f'{scan.id}.pdf')
    output_directory = os.path.join(data_directory, f'{scan.exam.id}_data')

    try:
        exam_config = exam_metadata(scan.exam.id)
    except Exception as e:
        report_error(f'Error while reading Exam metadata: {e}')
        raise

    with Pdf.open(pdf_path) as pdf_reader:
        total = len(pdf_reader.pages)

    failures = []
    try:
        for image, page in extract_images(pdf_path):
            report_progress(f'Processing page {page} / {total}')
            try:
                success, description = process_page(
                    image, exam_config, output_directory
                )
                if not success:
                    print(description)
                    failures.append(page)
            except Exception as e:
                report_error(f'Error processing page {page}: {e}')
                return
    except Exception as e:
        report_error(f"Failed to read pdf: {e}")
        raise

    if failures:
        processed = total - len(failures)
        if processed:
            report_error(
                f'Processed {processed} / {total} pages. '
                f'Failed on pages: {failures}'
            )
        else:
            report_error(f'Failed on all {total} pages.')
    else:
        report_success(f'Processed {total} pages.')


def exam_metadata(exam_id):
    """Read off exam token and barcode coordinates from the database."""
    # Raises exception if zero or more than one barcode widgets found
    barcode_widget = ExamWidget.query.filter(ExamWidget.exam_id == exam_id, ExamWidget.name == "barcode_widget").one()

    return ExamMetadata(
            token=barcode_widget.exam.token,
            barcode_coords=[
                max(0, barcode_widget.y),
                max(0, barcode_widget.y + 50),
                max(0, barcode_widget.x),
                max(0, barcode_widget.x + 50),
            ],
        )


def exam_student_id_widget(exam_id):
    """
    Get the student id widget and an array of it's coordinates for an exam.
    :param exam_id: the id of the exam to get the widget for
    :return: the student id widget, and an array of coordinates [ymin, ymax, xmin, xmax]
    """

    fontsize = current_app.config['ID_GRID_FONT_SIZE']
    margin = current_app.config['ID_GRID_MARGIN']
    digits = current_app.config['ID_GRID_DIGITS']
    id_grid_height = 12 * margin + 11 * fontsize
    id_grid_width = 5 * margin + 16 * fontsize + digits * (fontsize + margin)

    student_id_widget = ExamWidget.query.filter(ExamWidget.exam_id == exam_id,
                                                ExamWidget.name == "student_id_widget").one()
    student_id_widget_coords = [
        student_id_widget.y,  # top
        student_id_widget.y + id_grid_height,  # bottom
        student_id_widget.x,  # left
        student_id_widget.x + id_grid_width,  # right
    ]
    return student_id_widget, student_id_widget_coords


def write_pdf_status(scan_id, status, message):
    scan = Scan.query.get(scan_id)
    scan.status = status
    scan.message = message
    db.session.commit()


def process_page(image_data, exam_config, output_dir=None, strict=False):
    """Incorporate a scanned image in the data structure.

    For each page perform the following steps:
    1. Correct the image, using the corner markers to align:
        1.1. deskew
        2.2. shift
    2. Extract the page barcode
    3. Verify it satisfies the format required by zesje
    4. Verify it belongs to the correct exam
    5. Incorporate the page in the database
    6. Perform pregrading
    7. If the page contains student number, try to read it off the page

    Parameters
    ----------
    image_data : PIL Image
    exam_config : ExamMetadata instance
        Information about the exam to which this page should belong
    output_dir : string, optional
        Path where the processed image must be stored. If not provided, don't
        save the result and don't modify the database.
    strict : bool
        Whether to stop trying if we did not find corner markers.
        This spoils page positioning, but may increase the success rate.

    Returns
    -------
    success : bool
    description : string
        What has happened.

    Raises
    ------
    ValueError if the page is from a wrong exam.

    Notes
    -----
    A page from a wrong exam likely means we're reading a wrong pdf, and
    therefore should stop processing any other pages if this function raises.
    """
    image_array = np.array(image_data)
    shape = image_array.shape
    if shape[0] < shape[1]:
        # Handle possible horizontal image orientation.
        image_array = np.array(np.rot90(image_array, -1))

    try:
        barcode, upside_down = decode_barcode(image_array, exam_config)
        if upside_down:
            # TODO: check if view errors appear
            image_array = np.array(image_array[::-1, ::-1])
    except RuntimeError:
        return False, "Reading barcode failed"

    if barcode.token != exam_config.token:
        raise ValueError("PDF is not from this exam")

    dpi = guess_dpi(image_array)
    exam = Exam.query.filter(Exam.token == exam_config.token).one()

    reference = reference_image(exam.id, barcode.page, dpi)
    reference_shape = reference.shape[0:2]

    try:
        corner_keypoints = find_corner_marker_keypoints(image_array)
        image_array = realign_image(image_array, reference_shape, corner_keypoints)
    except RuntimeError as e:
        if strict:
            return False, str(e)
        else:
            # Resize the image to match the reference
            image_array = resize_image(image_array, reference_shape)

    if output_dir is not None:
        image_path = save_image(image_array, barcode=barcode, base_path=output_dir)
    else:
        return True, "Testing, image not saved and database not updated."

    sub = update_database(image_path, barcode)

    try:
        grade_problem(sub, barcode.page, image_array)
    except InternalError as e:
        if strict:
            return False, str(e)

    if barcode.page == 0:
        description = guess_student(
            exam_token=barcode.token, copy_number=barcode.copy
        )
    else:
        description = "Scanned page doesn't contain student number."

    if sub.student:
        ungrade_multiple_sub(sub.student.id, sub.exam_id)

    return True, description


def save_image(image, barcode, base_path):
    """Save an image at an appropriate location.

    Parameters
    ----------
    image : numpy array
        Image data.
    barcode : ExtractedBarcode
        The barcode identifying the page.
    base_path : string
        The folder corresponding to a correct exam.

    Returns
    -------
    image_path : string
        Location of the image.
    """
    submission_path = os.path.join(base_path, 'submissions', f'{barcode.copy}')
    os.makedirs(submission_path, exist_ok=True)
    image_path = os.path.join(submission_path, f'page{barcode.page:02d}.jpg')
    Image.fromarray(image).save(image_path)
    return image_path


def update_database(image_path, barcode):
    """Add a database entry for the new image or update an existing one.

    Parameters
    ----------
    image_path : string
        Path to the image.
    barcode : ExtractedBarcode
        The data from the image barcode.

    Returns
    -------
    sub : Submission
        the current submission
    """
    exam = Exam.query.filter(Exam.token == barcode.token).first()
    if exam is None:
        raise RuntimeError('Invalid exam token.')

    sub = Submission.query.filter(Submission.copy_number == barcode.copy, Submission.exam_id == exam.id).one_or_none()
    if sub is None:
        sub = Submission(copy_number=barcode.copy, exam=exam)
        db.session.add(sub)
        for problem in exam.problems:
            db.session.add(Solution(problem=problem, submission=sub))

    # We may have added this page in previous uploads but we only want a single
    # 'Page' entry regardless
    if Page.query.filter(Page.submission == sub, Page.number == barcode.page).one_or_none() is None:
        rel_path = os.path.relpath(image_path, start=current_app.config['DATA_DIRECTORY'])
        db.session.add(Page(path=rel_path, submission=sub, number=barcode.page))

    db.session.commit()

    return sub


def decode_barcode(image, exam_config):
    """Extract a barcode from a PIL Image."""

    barcode_coords = exam_config.barcode_coords

    # TODO: use points as base unit
    barcode_coords_in = np.asarray(barcode_coords) / 72
    rotated = np.rot90(image, k=2)
    step_sizes = (1, 2)
    image_crop = get_box(image, barcode_coords_in, padding=1.5)
    image_crop_rotated = get_box(rotated, barcode_coords_in, padding=1.5)

    images = [
        (image[::step, ::step], ud)
        for step in step_sizes
        for (image, ud) in ((image_crop, False), (image_crop_rotated, True))
    ]

    # Transformations we apply to images in order to increase a chance of succsess.
    methods = [
        (lambda img: Image.fromarray(img)),
        (lambda img: Image.fromarray(img).point(lambda p: p > 100 and 255)),
        (lambda img: Image.fromarray(cv2.blur(img, (3, 3)))),
        (lambda img: (Image.fromarray(cv2.blur(img, (3, 3)))
                           .point(lambda p: p > 100 and 255))),
    ]

    for (image, upside_down), method in itertools.product(images, methods):
        results = pylibdmtx.decode(method(image))
        if len(results) == 1:
            data = results[0].data
            # See https://github.com/NaturalHistoryMuseum/pylibdmtx/issues/24
            try:
                data = data.decode('utf-8')
            except UnicodeDecodeError:
                data = decode_raw_datamatrix(data)

            try:
                token, copy, page = data.split('/')
                copy = int(copy)
                page = int(page)
                return ExtractedBarcode(token, copy, page), upside_down
            except ValueError:
                pass

    raise RuntimeError("No barcode found.")


def guess_student(exam_token, copy_number, force=False):
    """Update a submission with a guessed student number.

    Parameters
    ----------
    exam_token : string
        Unique exam identifier (see database schema).
    copy_number : int
        The copy number of the submission.
    force : bool
        Whether to update the student number of a submission with a validated
        signature, default False.

    Returns
    -------
    description : string
        Description of the outcome.
    """

    # Throws exception if zero or more than one of Exam, Submission or Page found
    exam = Exam.query.filter(Exam.token == exam_token).one()
    sub = Submission.query.filter(Submission.copy_number == copy_number,
                                  Submission.exam_id == exam.id).one()
    image_path = Page.query.filter(Page.submission_id == sub.id,
                                   Page.number == 0).one().abs_path

    student_id_widget, student_id_widget_coords = exam_student_id_widget(exam.id)

    if sub.signature_validated and not force:
        return "Signature already validated"

    try:
        number = get_student_number(image_path, student_id_widget_coords)
    except Exception as e:
        return "Failed to extract student number: " + str(e)

    student = Student.query.get(int(number))
    if student is not None:
        exam = Exam.query.filter(Exam.token == exam_token).one()
        sub = Submission.query.filter(Submission.copy_number == copy_number, Submission.exam_id == exam.id).one()
        sub.student = student
        db.session.commit()
        return "Successfully extracted student number"
    else:
        return f"Student number {number} not in the database"


def get_student_number(image_path, student_id_widget_coords):
    """Extract the student number from the image path with the scanned number.

    TODO: all the numerical parameters are guessed and work well on the first
    exam.  Yet, they should be inferred from the scans.
    """
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    # TODO: use points as base unit
    student_id_widget_coords_in = np.asarray(student_id_widget_coords) / 72
    image_raw = get_box(image, student_id_widget_coords_in, padding=0.3)

    # Add a 1 pixel border to floodfill from all sides
    h, w, *_ = image_raw.shape
    image = np.full((h+2, w+2), 255, np.uint8)
    image[1:-1, 1:-1] = image_raw

    _, thresholded = cv2.threshold(image, 150, 255, cv2.THRESH_BINARY)
    thresholded = cv2.bitwise_not(thresholded)

    # Copy the thresholded image.
    im_floodfill = thresholded.copy()

    # Mask used to flood filling.
    # Notice the size needs to be 2 pixels than the image.
    mask = np.zeros((h+4, w+4), np.uint8)

    # Floodfill from point (0, 0)
    cv2.floodFill(im_floodfill, mask, (0, 0), 255)

    # Invert floodfilled image
    im_floodfill_inv = cv2.bitwise_not(im_floodfill)

    # Combine the two images to get the foreground.
    im_out = ~(thresholded | im_floodfill_inv)

    min_box_size = int(h*w/1000)

    params = cv2.SimpleBlobDetector_Params()
    params.filterByArea = True
    params.minArea = min_box_size * 0.7
    params.maxArea = min_box_size * 2
    params.filterByCircularity = False
    params.filterByConvexity = True
    params.minConvexity = 0.87
    params.filterByInertia = True
    params.minInertiaRatio = 0.7

    detector = cv2.SimpleBlobDetector_create(params)

    keypoints = detector.detect(im_out)
    if len(keypoints) <= 2:
        raise ValueError('Blob detector did not detect enough keypoints.')

    centers = np.array(sorted([kp.pt for kp in keypoints])).astype(int)
    diameters = np.array([kp.size for kp in keypoints])
    r = int(np.median(diameters)/4)
    (right, bottom) = np.max(centers, axis=0)
    (left, top) = np.min(centers, axis=0)
    centers = np.mgrid[left:right:7j, top:bottom:10j].astype(int)
    weights = []
    for center in centers.reshape(2, -1).T:
        x, y = center
        weights.append(np.sum(255 - image[y-r:y+r, x-r:x+r]))

    weights = np.array(weights).reshape(10, 7, order='F')
    return sum(((np.argmax(weights, axis=0)) % 10)[::-1] * 10**np.arange(7))


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


def find_corner_marker_keypoints(image_array, corner_sizes=[0.125, 0.25, 0.5]):
    """Generates a list of OpenCV keypoints which resemble corner markers.
    This is done using a SimpleBlobDetector

    For each corner size it tries to find enough corner markers.
    If not enough are detected it continues with the next corner size
    until the list is depleted and raises a RunTimeError.

    Parameters:
    -----------
    image_data: 3d numpy array

    corner_sizes : list of float
        The corner sizes to search the corner markers in

    Returns
    -------
    corner_points : list of (int, int)
        The found corner markers, can contain 0-4 corner markers.
    """
    h, w, *_ = image_array.shape
    marker_length = current_app.config['MARKER_LINE_LENGTH'] * guess_dpi(image_array) / 72
    marker_width = current_app.config['MARKER_LINE_WIDTH'] * guess_dpi(image_array) / 72
    marker_area = marker_length * marker_width * 2
    marker_area_min = max(marker_length * (marker_width - 1) * 2, 0)  # One pixel thinner due to possible aliasing

    corner_points = []

    top_bottom = (True, False)
    left_right = (True, False)

    for is_top, is_left in itertools.product(top_bottom, left_right):
        corner_points_current_corner = []

        for corner_size in corner_sizes:
            # Filter out everything in the center of the image
            h_slice = slice(0, int(h*corner_size)) if is_top else slice(int(h*(1-corner_size)), h)
            w_slice = slice(0, int(w*corner_size)) if is_left else slice(int(w*(1-corner_size)), w)

            gray_im = cv2.cvtColor(image_array[h_slice, w_slice], cv2.COLOR_BGR2GRAY)
            _, inv_im = cv2.threshold(gray_im, 175, 255, cv2.THRESH_BINARY_INV)
            ret, labels = cv2.connectedComponents(inv_im)
            for label in range(1, ret):
                new_img = (labels == label)

                # Relative error determined to work well empirically
                max_error = 1.19

                blob_area = np.sum(new_img)
                if not marker_area_min / max_error**2 < blob_area < marker_area * max_error**2:
                    continue  # The area of the blob is too small or too large

                new_img_uint8 = new_img.astype(np.uint8)

                angle_resolution = 0.25 * np.pi/180
                spatial_resolution = 1
                max_angle = 15 * np.pi/180
                max_angle_error = 3 * np.pi/180
                threshold = int(marker_length * .9)

                lines_vertical_1 = cv2.HoughLines(new_img_uint8, rho=spatial_resolution, theta=angle_resolution,
                                                  threshold=threshold, min_theta=0, max_theta=max_angle)
                lines_vertical_2 = cv2.HoughLines(new_img_uint8, rho=spatial_resolution, theta=angle_resolution,
                                                  threshold=threshold, min_theta=np.pi-max_angle, max_theta=np.pi)
                lines_vertical = (lines_vertical_1, lines_vertical_2)
                if all(lines is None for lines in lines_vertical):
                    continue  # Didn't find any vertical lines
                lines_vertical = np.vstack(
                        (lines for lines in (lines_vertical) if lines is not None)
                    )
                lines_vertical = lines_vertical.reshape(-1, 2).T

                # The vertical lines can have both theta ≈ 0 or theta ≈ π, here we flip those
                # points to ensure that we end up with two reasonably contiguous regions.
                to_flip = lines_vertical[1] > 3*np.pi/4
                lines_vertical[1, to_flip] -= np.pi
                lines_vertical[0, to_flip] *= -1

                rho_v, theta_v = np.average(lines_vertical, axis=1)

                # Search for horizontal lines that are nearly perpendicular
                horizontal_angle = theta_v + np.pi/2
                lines_horizontal = cv2.HoughLines(new_img_uint8, spatial_resolution, angle_resolution, threshold,
                                                  min_theta=horizontal_angle - max_angle_error, max_theta=horizontal_angle + max_angle_error)
                if lines_horizontal is None:
                    continue  # Didn't find any horizontal lines

                lines_horizontal = lines_horizontal.reshape(-1, 2).T
                rho_h, theta_h = np.average(lines_horizontal, axis=1)

                marker_boundings = bounding_box_corner_markers(marker_length, theta_h, theta_v, is_top, is_left)
                invalid_dimensions = False
                for nonzero_indices, marker_bounding in zip(np.nonzero(new_img)[::-1], marker_boundings):
                    start = np.min(nonzero_indices)
                    end = np.max(nonzero_indices)
                    blob_length = end - start

                    if not marker_bounding / max_error < blob_length < marker_bounding * max_error:
                        invalid_dimensions = True  # The dimensions of the blob are too large
                        break
                if invalid_dimensions:
                    continue

                y, x = np.linalg.solve([[np.cos(theta_h), np.sin(theta_h)], [np.cos(theta_v), np.sin(theta_v)]],
                                       [rho_h, rho_v])
                # TODO: add failsafes
                if np.isnan(x) or np.isnan(y):
                    continue
                corner_points_current_corner.append((int(y) + w_slice.start, int(x) + h_slice.start))

            if len(corner_points_current_corner) == 1:
                corner_points.append(corner_points_current_corner[0])
                break

            if len(corner_points_current_corner) > 1:
                # More than one corner point found, ignore this corner
                break

    return corner_points


def realign_image(image_array, page_shape, keypoints=None):
    """
    Transform the image so that the keypoints match the reference.

    params
    ------
    image_array : numpy.array
        The image in the form of a numpy array.
    page_shape : numpy.array
        The desired shape of the realigned image in pixels
    keypoints : List[(int,int)]
        tuples of coordinates of the found keypoints, (x,y), in pixels. Can be a set of 3 or 4 tuples.
        if none are provided, they are found by using find_corner_marker_keypoints on the input image.
    returns
    -------
    return_array: numpy.array
        The image realigned properly.

    Raises
    ------
    RuntimeError if no corner markers are detected or provided
    """

    if not keypoints:
        keypoints = find_corner_marker_keypoints(image_array)

    keypoints = np.asarray(keypoints)

    if not len(keypoints):
        raise RuntimeError("No keypoints provided for alignment.")

    # generate the coordinates where the markers should be
    dpi = guess_dpi(image_array)
    reference_keypoints = original_corner_markers(dpi)

    # create a matrix with the distances between each keypoint and match the keypoint sets
    dists = spatial.distance.cdist(keypoints, reference_keypoints)

    idxs = np.argmin(dists, 1)  # apply to column 1 so indices for input keypoints
    adjusted_markers = reference_keypoints[idxs]

    if len(adjusted_markers) == 1:
        # Transformation matrix is just shifting
        x_shift, y_shift = np.subtract(adjusted_markers[0], keypoints[0])
        M = np.float32([[1, 0, x_shift],
                        [0, 1, y_shift]])
    else:
        # Let opencv estimate the transformation matrix
        M = cv2.estimateAffinePartial2D(keypoints, adjusted_markers, method=cv2.LMEDS)[0]

    rows, cols = page_shape

    # apply the transformation matrix and fill in the new empty spaces with white
    return_image = cv2.warpAffine(image_array, M, (cols, rows),
                                  borderValue=(255, 255, 255, 255))

    return return_image


# Based on https://stackoverflow.com/a/49406095
def resize_image(image_array, page_shape):
    """
    Resize the image such that the dimensions match the reference.

    This is a fallback for realign image, when no keypoints are found.
    It maintains the aspect ratio and adds a white border when needed.

    params
    ------
    image_array : numpy.array
        The image in the form of a numpy array.
    page_shape : numpy.array
        The desired shape of the realigned image in pixels
    page_format : str
        The desired page format

    returns
    -------
    return_array: numpy.array
        The image resized properly.
    """
    sh, sw = page_shape

    h, w = image_array.shape[:2]

    if (h, w) == (sh, sw):
        return image_array

    # interpolation method
    if h > sh or w > sw:  # shrinking image
        interp = cv2.INTER_AREA

    else:  # stretching image
        interp = cv2.INTER_CUBIC

    # aspect ratio of image
    aspect = float(w)/h
    saspect = float(sw)/sh

    if (saspect > aspect):  # padding left and right
        new_h = sh
        new_w = np.round(new_h * aspect).astype(int)
        pad_horz = float(sw - new_w) / 2
        pad_left, pad_right = np.floor(pad_horz).astype(int), np.ceil(pad_horz).astype(int)
        pad_top, pad_bot = 0, 0

    elif (saspect < aspect):  # padding top and bottom
        new_w = sw
        new_h = np.round(new_w / aspect).astype(int)
        pad_vert = float(sh - new_h) / 2
        pad_top, pad_bot = np.floor(pad_vert).astype(int), np.ceil(pad_vert).astype(int)
        pad_left, pad_right = 0, 0

    else:  # only resize
        new_w, new_h = sw, sh
        pad_top, pad_bot, pad_left, pad_right = 0, 0, 0, 0

    # resize and and add border
    resized_img = cv2.resize(image_array, (new_w, new_h), interpolation=interp)
    resized_img = cv2.copyMakeBorder(resized_img, pad_top, pad_bot, pad_left, pad_right,
                                     borderType=cv2.BORDER_CONSTANT, value=(255, 255, 255))

    return resized_img


def original_corner_markers(dpi):
    page_size = current_app.config['PAGE_FORMATS'][current_app.config['PAGE_FORMAT']]

    margin = current_app.config['MARKER_MARGIN']
    left_x = margin/72 * dpi
    top_y = margin/72 * dpi
    right_x = (page_size[0] - margin) / 72 * dpi
    bottom_y = (page_size[1] - margin) / 72 * dpi

    return np.round([(left_x, top_y),
                     (right_x, top_y),
                     (left_x, bottom_y),
                     (right_x, bottom_y)])


def bounding_box_corner_markers(marker_length, theta1, theta2, top, left):
    """
    Computes the theoretical bounding box of a tilted corner marker.

    The result is only valid for a rotation up to 45 degrees.

    params
    ------
    marker_length : int
        The configured length of the corner marker in pixels
    theta1 : int
        Angle of the detected horizontal hough line
    theta2 : int
        Angle of the detected vertical hough line
    top : bool
        Whether the corner marker is at the top
    left : bool
        Whether the corner marker is at the left

    returns
    -------
    bounding_x, bounding_y : (int, int)
        The bounding box (in pixels) in x- and y-direction
    """
    bounding_x = marker_length * np.sin(theta1)
    bounding_y = marker_length * np.cos(theta2)

    bottom = not top
    right = not left

    if left and top and theta2 > 0:
        bounding_x += np.sin(theta2) * marker_length
    if left and bottom and theta2 < 0:
        bounding_x -= np.sin(theta2) * marker_length

    if right and top and theta2 < 0:
        bounding_x -= np.sin(theta2) * marker_length
    if right and bottom and theta2 > 0:
        bounding_x += np.sin(theta2) * marker_length

    if left and top and theta1 < np.pi/2:
        bounding_y += np.cos(theta1) * marker_length
    if left and bottom and theta1 > np.pi/2:
        bounding_y -= np.cos(theta1) * marker_length

    if right and top and theta1 > np.pi/2:
        bounding_y -= np.cos(theta1) * marker_length
    if right and bottom and theta1 < np.pi/2:
        bounding_y += np.cos(theta1) * marker_length

    return bounding_x, bounding_y
