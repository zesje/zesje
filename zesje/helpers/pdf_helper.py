import os
from collections import namedtuple, ChainMap
import functools
import itertools
import subprocess
import argparse
import shutil
import tempfile
import contextlib

import numpy as np
import pandas
import cv2
import zbar

from pony import orm

from . import yaml_helper
from ..models import db, PDF, Exam, Problem, Page, Student, Submission, Solution


ExtractedQR = namedtuple('ExtractedQR', ['name', 'page', 'sub_nr', 'coords'])
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

    with make_temp_directory() as tmpdir:
        # Extract pages as images
        report_progress('Extracting pages')
        try:
            images = pdf_to_images(pdf_path, tmpdir)
        except Exception as e:
            report_error(f'Error while extracting pages: {e}')
            raise

        # Extract QR codes.
        report_progress('Extracting page metadata')
        try:
            extracted_qrs = [extract_qr(image, config.version)
                             for image in images]
        except RuntimeError:
            report_error('Zesje version mismatch between config file and PDF')
            raise
        except Exception as e:
            report_error(f'Error while extracting QR codes: {e}')
            raise

        if any(qr[0] != config.exam_name for qr in extracted_qrs if qr is not None):
            report_error('PDF is not from this exam')
            return

        # Process individual pages, ensuring we report the page numbers
        # starting from 1.
        failures = []
        for i, (image, qr) in enumerate(1, zip(images, extracted_qrs)):
            report_progress(f'Processing page {i} / {len(images)}')
            if qr is None:
                failures.append(image)
                continue
            try:
                process_page(output_directory, image, qr, config)
            except Exception as e:
                print(image, e)
                failures.append(image)


        if failures:
            processed = len(images) - len(failures)
            # images are named like '-nnnnn.jpg'
            failures = [int(os.path.basename(im)[1:-4]) for im in failures]
            report_error(
                f'Processed {processed} / {len(images)} pages. '
                f'Failed on pages: {failures}'
            )
        else:
           report_success(f'processed {len(images)} pages')


def process_page(output_dir, image, qr_data, exam_config):
    assert qr_data is not None
    qr_coords, widget_data = exam_config.qr_coords, exam_config.widget_data

    rotate_and_shift(image, qr_data, qr_coords)
    sub_nr = qr_data.sub_nr

    with orm.db_session:
        exam = Exam.get(name=qr_data.name)
        sub = Submission.get(copy_number=sub_nr, exam=exam) \
              or Submission(copy_number=sub_nr, exam=exam)
        _, ext = os.path.splitext(image)
        target = os.path.join(output_dir, f'{qr_data.name}_{sub_nr}')
        os.makedirs(target, exist_ok=True)
        target_image = os.path.join(target, f'page{qr_data.page}{ext}')
        shutil.move(image, target_image)
        # We may have added this page in previous uploads; the above
        # 'rename' then overwrites the previosly uploaded page, but
        # we only want a single 'Page' entry.
        if Page.get(path=target_image, submission=sub) is None:
            Page(path=target_image, submission=sub)
        widgets_on_page = widget_data[widget_data.page == qr_data.page]
        for problem in widgets_on_page.index:
            if problem == 'studentnr':
                sub.signature_image_path = 'None'
                try:
                    number_widget = widgets_on_page.loc['studentnr']
                    number = get_student_number(target_image, number_widget)
                    sub.student = Student.get(id=int(number))
                except Exception:
                    pass  # could not extract student name
            else:
                prob = Problem.get(name=problem, exam=exam)
                sol = Solution.get(problem=prob, submission=sub)
                if sol:
                    sol.image_path = 'None'
                else:
                    Solution(problem=prob, submission=sub,
                             image_path='None')


def pdf_to_images(pdf_path, output_path):
    """Extract all images out of a pdf file."""
    # We convert everything to jpeg, which may be suboptimal, however some
    # formats recognized by pdfimages aren't understood by opencv.
    subprocess.run(['pdfimages', '-j', pdf_path, output_path])
    return sorted(os.path.join(output_path, f)
                  for f in os.listdir(output_path)
                  if f.endswith('.jpg'))


def write_pdf_status(pdf_id, status, message):
    with orm.db_session:
        pdf = PDF[pdf_id]
        pdf.status = status
        pdf.message = message
        

@contextlib.contextmanager
def make_temp_directory():
    temp_dir = tempfile.mkdtemp()
    if not temp_dir.endswith('/'):
        temp_dir += '/'
    try:
        yield temp_dir
    finally:
        shutil.rmtree(temp_dir)


def extract_qr(image_path, yaml_version, scale_factor=4):
    image = cv2.imread(image_path,
                       cv2.IMREAD_GRAYSCALE)[::scale_factor, ::scale_factor]
    if image.shape[0] < image.shape[1]:
        image = image.T
    # Varied thresholds because zbar is picky about contrast.
    for threshold in (200, 150, 220):
        thresholded = 255 * (image > threshold)
        # zbar also cares about orientation.
        for direction in itertools.product([1, -1], [1, -1]):
            flipped = thresholded[::direction[0], ::direction[1]]
            scanner = zbar.Scanner()
            results = scanner.scan(flipped.astype(np.uint8))
            if results:
                try:
                    version, name, page, copy = \
                                results[0].data.decode().split(';')
                except ValueError:
                    return
                if version != 'v{}'.format(yaml_version):
                    raise RuntimeError('Yaml format mismatch')
                coords = np.array(results[0].position)
                # zbar doesn't respect array ordering!
                if not np.isfortran(flipped):
                    coords = coords[:, ::-1]
                coords *= direction
                coords %= image.shape
                coords *= scale_factor
                return ExtractedQR(name, int(page), int(copy), coords)
    else:
        return


def guess_dpi(image_array):
    h, *_ = image_array.shape
    resolutions = np.array([1200, 600, 300, 200, 150, 120, 100, 75, 60, 50, 40])
    return resolutions[np.argmin(abs(resolutions - 25.4 * h / 297))]


def rotate_and_shift(image_path, extracted_qr, qr_coords):
    _, page, _, position = extracted_qr
    image = cv2.imread(image_path)

    if image.shape[0] < image.shape[1]:
        image = np.transpose(image, (1, 0, 2))

    dpi = guess_dpi(image)
    h, w, *_ = image.shape
    qr_widget = qr_coords[qr_coords.page == page]
    box = dpi * qr_widget[['top', 'bottom', 'left', 'right']].values[0]
    y0, x0 = h - np.mean(box[:2]), np.mean(box[2:])
    y, x = np.mean(position, axis=0)
    if (x > w / 2) != (x0 > w / 2):
        image = image[:, ::-1]
        x = w - x
    if (y > h / 2) != (y0 > h / 2):
        image = image[::-1]
        y = h - y

    shift = np.round((y0-y, x0-x)).astype(int)
    shifted_image = np.roll(image, shift[0], axis=0)
    shifted_image = np.roll(shifted_image, shift[1], axis=1)

    cv2.imwrite(image_path, shifted_image)


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
