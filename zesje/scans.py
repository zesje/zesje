import functools
import itertools
import math
import os
from collections import namedtuple, Counter
from io import BytesIO
import signal

import cv2
import numpy as np
import PyPDF2
from PIL import Image
from pylibdmtx import pylibdmtx

from .database import db, Scan, Exam, Page, Student, Submission, Solution, ExamWidget
from .datamatrix import decode_raw_datamatrix
from .images import guess_dpi, get_box
from .factory import make_celery
from .pregrader import add_feedback_to_solution

ExtractedBarcode = namedtuple('ExtractedBarcode', ['token', 'copy', 'page'])

ExamMetadata = namedtuple('ExamMetadata', ['token', 'barcode_coords'])

celery = make_celery()


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

    from flask import current_app
    app_config = current_app.config

    # We want to trigger an exit from within Python when a signal is received.
    # The default behaviour for SIGTERM is to terminate the process without
    # calling 'atexit' handlers, and SIGINT raises keyboard interrupt.
    for signal_type in (signal.SIGINT, signal.SIGTERM):
        signal.signal(signal_type, raise_exit)

    try:
        _process_pdf(scan_id, app_config)
    except BaseException as error:
        # TODO: When #182 is implemented, properly separate user-facing
        #       messages (written to DB) from developer-facing messages,
        #       which should be written into the log.
        write_pdf_status(scan_id, 'error', "Unexpected error: " + str(error))


def _process_pdf(scan_id, app_config):
    data_directory = app_config.get('DATA_DIRECTORY', 'data')

    report_error = functools.partial(write_pdf_status, scan_id, 'error')
    report_progress = functools.partial(write_pdf_status, scan_id, 'processing')
    report_success = functools.partial(write_pdf_status, scan_id, 'success')

    # Raises exception if zero or more than one scans found
    scan = Scan.query.filter(Scan.id == scan_id).one()

    pdf_path = os.path.join(data_directory, 'scans', f'{scan.id}.pdf')
    output_directory = os.path.join(data_directory, f'{scan.exam.id}_data')

    try:
        exam_config = exam_metadata(scan.exam.id)
    except Exception as e:
        report_error(f'Error while reading Exam metadata: {e}')
        raise

    total = PyPDF2.PdfFileReader(open(pdf_path, "rb")).getNumPages()
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
            raise RuntimeError(f'Page {pagenr + 1} contains more than 1 image,'
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

                if img.mode == 'L':
                    img = img.convert('RGB')
                yield img, pagenr+1


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
    6. If the page contains student number, try to read it off the page

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

    corner_keypoints = find_corner_marker_keypoints(image_array)
    try:
        check_corner_keypoints(image_array, corner_keypoints)
    except RuntimeError as e:
        if strict:
            return False, str(e)
    else:
        (image_array, new_keypoints) = rotate_image(image_array, corner_keypoints)
        image_array = shift_image(image_array, new_keypoints)

    try:
        barcode, upside_down = decode_barcode(image_array, exam_config)
        if upside_down:
            # TODO: check if view errors appear
            image_array = np.array(image_array[::-1, ::-1])
    except RuntimeError:
        return False, "Reading barcode failed"

    if barcode.token != exam_config.token:
        raise ValueError("PDF is not from this exam")

    if output_dir is not None:
        image_path = save_image(image_array, barcode=barcode, base_path=output_dir)
    else:
        return True, "Testing, image not saved and database not updated."

    update_database(image_path, barcode)
    add_feedback_to_solution(barcode.page, image_array, corner_keypoints)

    if barcode.page == 0:
        description = guess_student(
            exam_token=barcode.token, copy_number=barcode.copy
        )
    else:
        description = "Scanned page doesn't contain student number."

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
    signature_validated : bool
        If the corresponding submission has a validated signature.
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
        db.session.add(Page(path=image_path, submission=sub, number=barcode.page))

    db.session.commit()

    return sub, exam


def decode_barcode(image, exam_config):
    """Extract a barcode from a PIL Image."""

    barcode_coords = exam_config.barcode_coords

    # TODO: use points as base unit
    barcode_coords_in = np.asarray(barcode_coords) / 72
    rotated = np.rot90(image, k=2)
    step_sizes = (1, 2)
    image_crop = get_box(image, barcode_coords_in, padding=1.3)
    image_crop_rotated = get_box(rotated, barcode_coords_in, padding=1.3)

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


def rotate_image(image_array, corner_keypoints):
    """Rotate an image according to the rotation of the corner markers."""

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
    angle_deg = -1 * calc_angle(coords1, coords2)
    angle_rad = math.radians(angle_deg)

    h, w, *_ = image_array.shape
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

    # Create rotation matrix and rotate the image around the center
    rot_mat = cv2.getRotationMatrix2D(rot_origin, angle_deg, 1)
    rot_image = cv2.warpAffine(image_array, rot_mat, (w, h), cv2.BORDER_CONSTANT,
                               borderMode=cv2.BORDER_CONSTANT,
                               borderValue=(255, 255, 255))

    return (rot_image, after_rot_keypoints)


def shift_image(image, corner_keypoints):
    """Roll the image such that QR occupies coords
       specified by the template."""
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
            x = bottomleft[0][0]
            y = topright[0][1]

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

    return shifted_image


def guess_student(exam_token, copy_number, app_config=None, force=False):
    """Update a submission with a guessed student number.

    Parameters
    ----------
    exam_token : string
        Unique exam identifier (see database schema).
    copy_number : int
        The copy number of the submission.
    app_config : Flask config
        Optional.
    force : bool
        Whether to update the student number of a submission with a validated
        signature, default False.

    Returns
    -------
    description : string
        Description of the outcome.
    """
    if app_config is None:
        app_config = {}

    # Throws exception if zero or more than one of Exam, Submission or Page found
    exam = Exam.query.filter(Exam.token == exam_token).one()
    sub = Submission.query.filter(Submission.copy_number == copy_number,
                                  Submission.exam_id == exam.id).one()
    image_path = Page.query.filter(Page.submission_id == sub.id,
                                   Page.number == 0).one().path

    student_id_widget = ExamWidget.query.filter(ExamWidget.exam_id == exam.id,
                                                ExamWidget.name == "student_id_widget").one()
    student_id_widget_coords = [
            student_id_widget.y,  # top
            student_id_widget.y + app_config.get('ID_GRID_HEIGHT', 181),  # bottom
            student_id_widget.x,  # left
            student_id_widget.x + app_config.get('ID_GRID_WIDTH', 313),  # right
        ]

    if sub.signature_validated and not force:
        return "Signature already validated"

    try:
        number = get_student_number(image_path, student_id_widget_coords)
    except Exception:
        return "Failed to extract student number"

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
    image = get_box(image, student_id_widget_coords_in, padding=0.3)
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
    params.minArea = min_box_size * 0.7
    params.maxArea = min_box_size * 2
    params.filterByCircularity = False
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


def find_corner_marker_keypoints(image_array):
    """Generates a list of OpenCV keypoints which resemble corner markers.
    This is done using a SimpleBlobDetector

    Parameters:
    -----------
    image_data: Source image

    """
    h, w, *_ = image_array.shape
    marker_length = .8 / 2.54 * guess_dpi(image_array)  # 8 mm in inches × dpi
    marker_width = .1 / 2.54 * guess_dpi(image_array)  # should get exact width

    # Filter out everything in the center of the image
    tb = slice(0, h//8), slice(7*h//8, h)
    lr = slice(0, w//8), slice(7*w//8, w)
    corner_points = []
    for corner in itertools.product(tb, lr):
        gray_im = cv2.cvtColor(image_array[corner], cv2.COLOR_BGR2GRAY)
        _, bin_im = cv2.threshold(gray_im, 150, 255, cv2.THRESH_BINARY)
        img = bin_im
        ret, labels = cv2.connectedComponents(~img)
        for label in range(1, ret):
            new_img = (labels == label)
            if np.sum(new_img) > marker_length * marker_width * 2:
                continue  # The blob is too large
            lines = cv2.HoughLines(new_img.astype(np.uint8), 1, np.pi/180, int(marker_length * .9))
            if lines is None:
                continue  # Didn't find any lines
            lines = lines.reshape(-1, 2).T

            # One of the lines is nearly horizontal, can have both theta ≈ 0 or theta ≈ π;
            # here we flip those points to ensure that we end up with two reasonably contiguous regions.
            to_flip = lines[1] > 3*np.pi/4
            lines[1, to_flip] -= np.pi
            lines[0, to_flip] *= -1
            v = (lines[1] > np.pi/4)
            if np.all(v) or not np.any(v):
                continue
            rho1, theta1 = np.average(lines[:, v], axis=1)
            rho2, theta2 = np.average(lines[:, ~v], axis=1)
            y, x = np.linalg.solve([[np.cos(theta1), np.sin(theta1)], [np.cos(theta2), np.sin(theta2)]], [rho1, rho2])
            # TODO: add failsafes
            if np.isnan(x) or np.isnan(y):
                continue
            corner_points.append((int(y) + corner[1].start, int(x) + corner[0].start))

    return corner_points


def check_corner_keypoints(image_array, keypoints):
    """Checks whether the corner markers are valid.

    1. Checks that there are between 3 and 4 corner markers.
    2. Checks that no 2 corner markers are the same corner of the image.

    Parameters:
    -----------
    image_array : source image
    keypoints : list of tuples containing the coordinates of keypoints
    """
    total = len(keypoints)
    if total < 3:
        raise RuntimeError(f"Too few corner markers found ({total}).")
    elif total > 4:
        raise RuntimeError(f"Too many corner markers found ({total}).")

    h, w, *_ = image_array.shape

    corners = Counter((x < (w / 2), (y < h / 2)) for x, y in keypoints)

    if max(corners.values()) > 1:
        raise RuntimeError("Found multiple corner markers in the same corner")
