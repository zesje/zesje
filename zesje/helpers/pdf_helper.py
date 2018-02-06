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

from flask import current_app as app
from pony import orm

from . import yaml_helper
from ..models import db, PDF, Exam, Problem, Page, Student, Submission, Solution


ExtractedQR = namedtuple('ExtractedQR', ['name', 'page', 'sub_nr', 'coords'])
ExamMetadata = namedtuple('ExamMetadata',
                          ['version', 'exam_name', 'qr_coords', 'widget_data'])


def process_pdf(pdf_id):
    """Process a PDF, recording progress to a database

    This *must* be called from a subprocess of the
    Flask process, so that we inherit the bound DB instance
    and the app config.

    Parameters
    ----------
    pdf_id : int
        The ID in the database of the PDF to process
    """
    data_directory = app.config['DATA_DIRECTORY']

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

        # Process individual pages
        failures = []
        for i, (image, qr) in enumerate(zip(images, extracted_qrs)):
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
        os.rename(image, target_image)
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
