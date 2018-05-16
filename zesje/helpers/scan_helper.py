import os
from collections import namedtuple, ChainMap
import functools
import itertools
import argparse
from io import BytesIO

import numpy as np
import pandas
import cv2
import zbar
from PIL import Image
import PyPDF2

from pony import orm

from . import yaml_helper
from ..models import db, PDF, Exam, Problem, Page, Student, Submission, Solution


ExtractedQR = namedtuple('ExtractedQR',
                         ['version', 'name', 'page', 'sub_nr', 'coords'])
ExamMetadata = namedtuple('ExamMetadata',
                          ['version', 'exam_name', 'qr_coords', 'widget_data'])


def process_pdf(pdf_id, data_directory):
    """Process a PDF, recording progress to a database

    This *must* be called from a subprocess of the
    Flask process, so that we inherit the bound DB instance
    and the app config.

    Parameters
    ----------
    pdf_id : int
        The ID in the database of the PDF to process
    data_directory : str
        The absolute path to the data directory on disk
    """

    # Ensure we are not inheriting a bound database, which is dangerous and
    # might be locked.
    db.bind('sqlite', os.path.join(data_directory, 'course.sqlite'))
    db.generate_mapping(create_tables=True)

    report_error = functools.partial(write_pdf_status, pdf_id, 'error')
    report_progress = functools.partial(write_pdf_status, pdf_id, 'processing')
    report_success = functools.partial(write_pdf_status, pdf_id, 'success')

    with orm.db_session:
        pdf = PDF[pdf_id]

        # TODO: paths
        pdf_filename = f'{pdf.id}.pdf'
        pdf_path = os.path.join(data_directory, 'pdfs', pdf_filename)
        config_path = os.path.join(data_directory, pdf.exam.yaml_path)
        output_directory = os.path.join(data_directory, pdf.exam.name + '_data')

    try:
        # Read in exam metadata
        config = ExamMetadata(*yaml_helper.parse(yaml_helper.read(config_path)))
    except Exception as e:
        report_error(f'Error while reading Exam metadata: {e}')
        raise

    total = PyPDF2.PdfFileReader(open(pdf_path, "rb")).getNumPages()
    failures = []
    try:
        for image, page in extract_images(pdf_path):
            report_progress(f'Processing page {page} / {total}')
            try:
                success, reason = process_page(output_directory, image, config)
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


def write_pdf_status(pdf_id, status, message):
    with orm.db_session:
        pdf = PDF[pdf_id]
        pdf.status = status
        pdf.message = message


def process_page(output_dir, image_data, exam_config):
    """Incorporate a scanned image in the data structure.

    For each page perform the following steps:
    1. Extract the page QR code
    2. Verify it satisfies the format required by zesje
    3. Verify it belongs to the correct exam
    4. Correct the image so that the coordinates are best aligned with the
       yaml (currently uses only QR code position)
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
    ext = image_data.format
    image_data.load()
    qr_data = extract_qr(image_data)

    if qr_data is None:
        return False, "Reading QR code failed"
    elif qr_data.version != f'v{exam_config.version}':
        raise ValueError('Zesje version mismatch between config file and PDF')
    elif qr_data.name != exam_config.exam_name:
        raise ValueError('PDF is not from this exam')

    qr_coords, widget_data = exam_config.qr_coords, exam_config.widget_data

    image_data = rotate_and_shift(image_data, qr_data, qr_coords)
    sub_nr = qr_data.sub_nr

    target = os.path.join(output_dir, f'{qr_data.name}_{sub_nr}')
    os.makedirs(target, exist_ok=True)
    target_image = os.path.join(target, f'page{qr_data.page}.jpg')
    image_data.save(target_image)

    with orm.db_session:
        exam = Exam.get(name=qr_data.name)
        sub = Submission.get(copy_number=sub_nr, exam=exam)

        if sub is None:
            sub = Submission(copy_number=sub_nr, exam=exam,
                             signature_image_path='None')

            for problem in widget_data.index:
                if problem == 'studentnr':
                    continue

                prob = Problem.get(name=problem, exam=exam)
                Solution(problem=prob, submission=sub, image_path='None')

        # We may have added this page in previous uploads; the above then
        # overwrites the previosly uploaded page, but we only want a single
        # 'Page' entry.
        if Page.get(path=target_image, submission=sub) is None:
            Page(path=target_image, submission=sub)

        if sub.signature_validated:
            # Nothing to update in the db
            return True, ''

    number_widget = widget_data.loc['studentnr']
    if qr_data.page == number_widget.page:
        try:
            number = get_student_number(target_image, number_widget)
        except Exception:
            return True, ''  # could not extract student name

        with orm.db_session:
            exam = Exam.get(name=qr_data.name)
            sub = Submission.get(copy_number=sub_nr, exam=exam)
            sub.student = Student.get(id=int(number))

    return True, ''


def extract_qr(image_data):
    """Extract a QR code from a PIL Image."""
    grayscale = np.asarray(image_data.convert(mode='L'))

    # Empirically we observed that the most important parameter
    # for zbar to successfully read a qr code is the resolution
    # controlled below by scaling the image by factor.
    # zbar also seems to care about image orientation, hence
    # the loop over dirx/diry.
    for dirx, diry, factor in itertools.product([1, -1], [1, -1], [8, 5, 4, 3]):
        scaled = grayscale[::factor * dirx, ::factor * diry]
        scanner = zbar.Scanner()
        # Filter only QR codes to eliminate some false positives.
        results = [i for i in scanner.scan(scaled) if i.type == 'QR-Code']
        if len(results) > 1:
            raise RuntimeError("Found > 1 QR code on the page.")
        if results:
            try:
                version, name, page, copy = \
                            results[0].data.decode().split(';')
            except ValueError:
                return
            coords = np.array(results[0].position)
            # zbar doesn't respect array ordering!
            coords *= [factor * dirx, factor * diry]
            coords %= grayscale.shape
            return ExtractedQR(version, name, int(page), int(copy), coords)
    else:
        return


def guess_dpi(image_array):
    h, *_ = image_array.shape
    resolutions = np.array([1200, 600, 300, 200, 150, 120, 100, 75, 60, 50, 40])
    return resolutions[np.argmin(abs(resolutions - 25.4 * h / 297))]

def shift_image(image_data, extracted_qr, qr_coords):
    """Roll the image such that QR occupies coords specified by the template."""
    page, position = extracted_qr.page, extracted_qr.coords
    y, x = np.mean(position, axis=0)
    image = np.array(image_data)

    if image.shape[0] < image.shape[1]:
        image = np.transpose(image, [1, 0] + [2] * (len(image.shape) > 2))
        x, y = y, x

    dpi = guess_dpi(image)
    h, w, *_ = image.shape
    qr_widget = qr_coords[qr_coords.page == page]
    box = dpi * qr_widget[['top', 'bottom', 'left', 'right']].values[0]
    y0, x0 = h - np.mean(box[:2]), np.mean(box[2:])
    if (x > w / 2) != (x0 > w / 2):
        image = image[:, ::-1]
        x = w - x
    if (y > h / 2) != (y0 > h / 2):
        image = image[::-1]
        y = h - y

    shift = np.round((y0-y, x0-x)).astype(int)
    shifted_image = np.roll(image, shift[0], axis=0)
    shifted_image = np.roll(shifted_image, shift[1], axis=1)

    # Workaround of https://github.com/python-pillow/Pillow/issues/3109
    if shifted_image.dtype == bool:
        shifted_image = shifted_image * np.uint8(255)

    return Image.fromarray(shifted_image)


def get_student_number(image_path, widget):
    """Extract the student number from the image path with the scanned number.

    TODO: all the numerical parameters are guessed and work well on the first
    exam.  Yet, they should be inferred from the scans.
    """
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    box = (widget.top, widget.bottom, widget.left, widget.right)
    image = get_box(image, box, padding=0.3)
    _, thresholded = cv2.threshold(image, 150, 255, cv2.THRESH_BINARY)
    thresholded = cv2.bitwise_not(thresholded)

    # Copy the thresholded image.
    im_floodfill = thresholded.copy()

    # Mask used to flood filling.
    # Notice the size needs to be 2 pixels than the image.
    h, w, *_ = thresholded.shape
    mask = np.zeros((h+2, w+2), np.uint8)

    # Floodfill from point (0, 0)
    cv2.floodFill(im_floodfill, mask, (0,0), 255);

    # Invert floodfilled image
    im_floodfill_inv = cv2.bitwise_not(im_floodfill)

    # Combine the two images to get the foreground.
    im_out = ~(thresholded | im_floodfill_inv)

    params = cv2.SimpleBlobDetector_Params()
    params.filterByArea = True
    params.minArea = 500
    params.maxArea = 1500
    params.filterByCircularity = True
    params.minCircularity = 0.01
    params.filterByConvexity = True
    params.minConvexity = 0.87
    params.filterByInertia = True
    params.minInertiaRatio = 0.7

    detector = cv2.SimpleBlobDetector_create(params)

    keypoints = detector.detect(im_out)
    centers = np.array(sorted([kp.pt for kp in keypoints])).astype(int)
    right, bottom = np.max(centers, axis=0)
    left, top = np.min(centers, axis=0)
    centers = np.mgrid[left:right:10j, top:bottom:7j].astype(int)
    weights = []
    for center in centers.reshape(2, -1).T:
        x, y = center
        r = 12
        weights.append(np.sum(255 - image[y-r:y+r, x-r:x+r]))
    weights = np.array(weights).reshape(10, 7)
    return sum(((np.argmax(weights, axis=0) + 1) % 10)[::-1] * 10**np.arange(7))


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
