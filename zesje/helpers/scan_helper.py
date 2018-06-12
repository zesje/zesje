import os
import platform
from collections import namedtuple, ChainMap
import functools
import itertools
import argparse
from io import BytesIO

import numpy as np
import pandas
import cv2
from pylibdmtx import pylibdmtx
import math
from PIL import Image
import PyPDF2

from pony import orm

from . import image_helper
from .datamatrix_helper import decode_raw_datamatrix
from ..models import db, Scan, Exam, Problem, Page, Student, Submission, Solution


ExtractedBarcode = namedtuple('ExtractedBarcode',
                              ['token', 'copy', 'page'])

ExamMetadata = namedtuple('ExamMetadata',
                          ['token', 'barcode_area', 'student_id_widget_area', 'problem_ids'])


def process_pdf(scan_id, app_config):
    """Process a PDF, recording progress to a database

    This *must* be called from a subprocess of the
    Flask process, so that we inherit the bound DB instance
    and the app config.

    Parameters
    ----------
    scan_id : int
        The ID in the database of the Scan to process
    app_config : obj
        The Flask app config
    """

    data_directory = app_config.get('DATA_DIRECTORY', 'data')
    # Ensure we are not inheriting a bound database, which is dangerous and
    # might be locked.
    db.bind('sqlite', os.path.join(data_directory, 'course.sqlite'))
    db.generate_mapping(create_tables=True)

    report_error = functools.partial(write_pdf_status, scan_id, 'error')
    report_progress = functools.partial(write_pdf_status, scan_id, 'processing')
    report_success = functools.partial(write_pdf_status, scan_id, 'success')

    with orm.db_session:
        scan = Scan[scan_id]

        pdf_path = os.path.join(data_directory, 'scans', f'{scan.id}.pdf')
        output_directory = os.path.join(data_directory, f'{scan.exam.id}_data')

        try:
            # Read in exam metadata
            student_id_widget = next(
                widget
                for widget
                in scan.exam.widgets
                if widget.name == 'student_id_widget'
            )
            barcode_widget = next(
                widget
                for widget
                in scan.exam.widgets
                if widget.name == 'barcode_widget'
            )
            exam_config = ExamMetadata(
                token=scan.exam.token,
                barcode_area=[
                    max(0, barcode_widget.y),
                    max(0, barcode_widget.y + 50),
                    max(0, barcode_widget.x),
                    max(0, barcode_widget.x + 50),
                ],
                student_id_widget_area=[
                    student_id_widget.y,  # top
                    student_id_widget.y + app_config.get('ID_GRID_HEIGHT', 181),  # bottom
                    student_id_widget.x,  # left
                    student_id_widget.x + app_config.get('ID_GRID_WIDTH', 313),  # right
                ],
                problem_ids=[
                    problem.id for problem in scan.exam.problems
                ]
            )
        except Exception as e:
            report_error(f'Error while reading Exam metadata: {e}')
            raise

    total = PyPDF2.PdfFileReader(open(pdf_path, "rb")).getNumPages()
    failures = []
    try:
        for image, page in extract_images(pdf_path):
            report_progress(f'Processing page {page} / {total}')
            try:
                success, reason = process_page(output_directory, image, exam_config)
                if not success:
                    print(reason)
                    failures.append(page)
            except Exception as e:
                report_error(f'Error processing page {page}: {e}')
                return
    except Exception as e:
        report_error(f"Failed to read pdf: {e}")
        raise

    if failures:
        processed = total - len(failures)
        report_error(
            f'Processed {processed} / {total} pages. '
            f'Failed on pages: {failures}'
        )
    else:
        report_success(f'processed {total} pages')


def extract_images(filename):
    """Yield all images from a PDF file.

    Adapted from https://stackoverflow.com/a/34116472/2217463

    We raise if there are > 1 images / page
    """
    reader = PyPDF2.PdfFileReader(open(filename, "rb"))
    total = reader.getNumPages()
    for pagenr in range(total):
        page = reader.getPage(pagenr)
        xObject = page['/Resources']['/XObject'].getObject()

        if sum((xObject[obj]['/Subtype'] == '/Image')
               for obj in xObject) > 1:
            raise RuntimeError('Page {pagenr} contains more than 1 image,'
                               'likely not a scan')

        for obj in xObject:
            if xObject[obj]['/Subtype'] == '/Image':
                data = xObject[obj].getData()
                filter = xObject[obj]['/Filter']

                if filter == '/FlateDecode':
                    size = (xObject[obj]['/Width'], xObject[obj]['/Height'])
                    if xObject[obj]['/ColorSpace'] == '/DeviceRGB':
                        mode = "RGB"
                    else:
                        mode = "P"
                    img = Image.frombytes(mode, size, data)
                else:
                    img = Image.open(BytesIO(data))

                yield img, pagenr+1


def write_pdf_status(scan_id, status, message):
    with orm.db_session:
        scan = Scan[scan_id]
        scan.status = status
        scan.message = message


def process_page(output_dir, image_data, exam_config):
    """Incorporate a scanned image in the data structure.

    For each page perform the following steps:
    1. Extract the page barcode
    2. Verify it satisfies the format required by zesje
    3. Verify it belongs to the correct exam
    4. Correct the image, using the corner markers to align:
        4.1. deskew
        4.2. shift
    5. Incorporate the page in the database
    6. If the page contains student number, try to read it off the page

    Parameters
    ----------
    output_dir : string
        Path where the processed image must be stored.
    image_data : PIL Image
    exam_config : ExamMetadata instance
        Information about the exam to which this page should belong

    Returns
    -------
    success : bool
    reason : string
        Reason for failure

    Raises
    ------
    RuntimeError if any of the steps 1-3 fail.

    Notes
    -----
    Because the failure of steps 1-3 likely means we're reading a wrong pdf, we
    should stop processing any other pages if this function raises.
    """

    barcode_data = decode_barcode(image_data, exam_config)

    if barcode_data is None:
        return False, "Reading barcode failed"
    elif barcode_data.token != exam_config.token:
        raise ValueError('PDF is not from this exam')

    image_array = np.array(image_data)

    corner_keypoints = image_helper.find_corner_marker_keypoints(image_data)
    image_helper.check_corner_keypoints(image_array, corner_keypoints)
    (image_data, new_keypoints) = rotate_image(image_data, corner_keypoints)
    image_data = shift_image(image_data, new_keypoints)

    target = os.path.join(output_dir, 'submissions', f'{barcode_data.copy}')
    os.makedirs(target, exist_ok=True)
    target_image = os.path.join(target, f'page{barcode_data.page:02d}.jpg')
    image_data.save(target_image)

    with orm.db_session:
        exam = Exam.get(token=barcode_data.token)
        sub = Submission.get(copy_number=barcode_data.copy, exam=exam)

        if sub is None:
            sub = Submission(copy_number=barcode_data.copy, exam=exam,
                             signature_image_path='None')

            for problem_id in exam_config.problem_ids:
                prob = Problem.get(id=problem_id)
                Solution(problem=prob, submission=sub, image_path='None')

        # We may have added this page in previous uploads; the above then
        # overwrites the previosly uploaded page, but we only want a single
        # 'Page' entry.
        if Page.get(path=target_image, submission=sub) is None:
            Page(path=target_image, submission=sub)

        if sub.signature_validated:
            # Nothing to update in the db
            return True, ''

    if barcode_data.page is 0:
        try:
            number = get_student_number(target_image, exam_config)
        except Exception:
            return True, ''  # could not extract student name

        with orm.db_session:
            exam = Exam.get(token=barcode_data.token)
            sub = Submission.get(copy_number=barcode_data.copy, exam=exam)
            student = Student.get(id=int(number))
            sub.student = student

    return True, ''


def decode_barcode(image, exam_config):
    """Extract a barcode from a PIL Image."""

    barcode_area = exam_config.barcode_area

    # TODO: use points as base unit
    barcode_area_in = np.asarray(barcode_area) / 72

    grayscale = np.asarray(image.convert(mode='L'))

    image_crop = image_helper.get_box(grayscale, barcode_area_in, padding=0.3)

    results = pylibdmtx.decode(image_crop)

    if results:
        if len(results) > 1:
            # we shouldn't read multiple codes
            raise
        try:
            data = results[0].data
            #  See https://github.com/NaturalHistoryMuseum/pylibdmtx/issues/24
            if 'Darwin' == platform.system():
                data = decode_raw_datamatrix(data)
            else:
                data = data.decode('utf-8')

            token, copy, page = data.split('/')
            copy = int(copy)
            page = int(page)
        except ValueError:
            return

        return ExtractedBarcode(token, copy, page)
    else:
        return


def guess_dpi(image_array):
    h, *_ = image_array.shape
    resolutions = np.array([1200, 600, 300, 200, 150, 120, 100, 75, 60, 50, 40])
    return resolutions[np.argmin(abs(resolutions - 25.4 * h / 297))]


def rotate_image(image_data, corner_keypoints):
    """Rotate a PIL image according to the rotation of the corner markers."""

    color_im = cv2.cvtColor(np.array(image_data), cv2.COLOR_RGB2BGR)

    # Find two corner markers which lie in the same horizontal half.
    # Same horizontal half is chosen as the line from one keypoint to
    # the other shoud be 0. To get corner markers in the same horizontal half,
    # the pair with the smallest distance is chosen.
    distances = [(a, b, math.hypot(a[0] - b[0], a[1] - b[1]))
                 for (a, b)
                 in list(itertools.combinations(corner_keypoints, 2))]
    distances.sort(key=lambda tup: tup[2], reverse=True)
    best_keypoint_combination = distances.pop()

    (coords1, coords2, dist) = best_keypoint_combination

    # If the angle is downward, we have a negative angle and
    # we want to rotate it counterclockwise
    # However warpaffine needs a positve angle if
    # you want to rotate it counterclockwise
    # So we invert the angle retrieved from calc_angle
    angle_deg = -1 * image_helper.calc_angle(coords1, coords2)
    angle_rad = math.radians(angle_deg)

    h, w, *_ = color_im.shape
    rot_origin = (w / 2, h / 2)

    keyp_from_rot_origin = [(coord_x - rot_origin[0], coord_y - rot_origin[1])
                            for (coord_x, coord_y)
                            in corner_keypoints]

    after_rot_keypoints = [((coord_y * math.sin(angle_rad) +
                            coord_x * math.cos(angle_rad) + rot_origin[0]),
                            (coord_y * math.cos(angle_rad) -
                            coord_x * math.sin(angle_rad)) + rot_origin[1])
                           for (coord_x, coord_y)
                           in keyp_from_rot_origin]

    color_im = cv2.cvtColor(np.array(image_data), cv2.COLOR_RGB2BGR)

    # Create rotation matrix and rotate the image around the center
    rot_mat = cv2.getRotationMatrix2D(rot_origin, angle_deg, 1)
    rot_image = cv2.warpAffine(color_im, rot_mat, (w, h), cv2.BORDER_CONSTANT,
                               borderMode=cv2.BORDER_CONSTANT,
                               borderValue=(255, 255, 255))

    return (Image.fromarray(cv2.cvtColor(rot_image, cv2.COLOR_BGR2RGB)),
            after_rot_keypoints)


def shift_image(image_data, corner_keypoints):
    """Roll the image such that QR occupies coords
       specified by the template."""
    image = np.array(image_data)
    corner_keypoints = np.array(corner_keypoints)
    h, w, *_ = image.shape

    xkeypoints = np.array([keypoint[0] for keypoint in corner_keypoints])
    ykeypoints = np.array([keypoint[1] for keypoint in corner_keypoints])

    is_left_half = xkeypoints < (w / 2)
    is_top_half = ykeypoints < (h / 2)

    # Get pixel locations to translate to. Currently only works with A4 sized
    # paper
    # TODO Add US letter functionality
    x0 = 10/210 * w
    y0 = 10/297 * h

    # If there is a keypoint in the topleft, take that point as starting point
    # for the translation
    topleft = corner_keypoints[is_left_half & is_top_half]
    if(len(topleft) == 1):
        x = topleft[0][0]
        y = topleft[0][1]
    else:

        # If there is no keypoint in the topleft, try to check if there is one
        # in the bottom left and bottom right. If so, infer the topleft
        # coordinates from their coordinates
        topright = corner_keypoints[~is_left_half & is_top_half]
        bottomleft = corner_keypoints[is_left_half & ~is_top_half]
        if(len(topright) == 1 & len(bottomleft) == 1):
            x = bottomleft[0]
            y = topright[1]

        else:
            # We can only end here if something went wrong with the detection
            # of corner markers. If so, just don't shift at all.
            x = x0
            y = y0

    shift = np.round((y0-y, x0-x)).astype(int)
    shifted_image = np.roll(image, shift[0], axis=0)
    shifted_image = np.roll(shifted_image, shift[1], axis=1)

    # Workaround of https://github.com/python-pillow/Pillow/issues/3109
    if shifted_image.dtype == bool:
        shifted_image = shifted_image * np.uint8(255)

    return Image.fromarray(shifted_image)


def get_student_number(image_path, exam_config):
    """Extract the student number from the image path with the scanned number.

    TODO: all the numerical parameters are guessed and work well on the first
    exam.  Yet, they should be inferred from the scans.
    """
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    # TODO: use points as base unit
    student_id_widget_area_in = np.asarray(exam_config.student_id_widget_area) / 72
    image = image_helper.get_box(image, student_id_widget_area_in, padding=0.0)
    _, thresholded = cv2.threshold(image, 150, 255, cv2.THRESH_BINARY)
    thresholded = cv2.bitwise_not(thresholded)

    # Copy the thresholded image.
    im_floodfill = thresholded.copy()

    # Mask used to flood filling.
    # Notice the size needs to be 2 pixels than the image.
    h, w, *_ = thresholded.shape
    mask = np.zeros((h+2, w+2), np.uint8)

    # Floodfill from point (0, 0)
    cv2.floodFill(im_floodfill, mask, (0, 0), 255)

    # Invert floodfilled image
    im_floodfill_inv = cv2.bitwise_not(im_floodfill)

    # Combine the two images to get the foreground.
    im_out = ~(thresholded | im_floodfill_inv)

    min_box_size = int(h*w/1000)

    params = cv2.SimpleBlobDetector_Params()
    params.filterByArea = True
    params.minArea = min_box_size
    params.maxArea = min_box_size * 2
    params.filterByCircularity = True
    params.minCircularity = 0.1
    params.maxCircularity = 0.8
    params.filterByConvexity = True
    params.minConvexity = 0.87
    params.filterByInertia = True
    params.minInertiaRatio = 0.7

    detector = cv2.SimpleBlobDetector_create(params)

    keypoints = detector.detect(im_out)
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
