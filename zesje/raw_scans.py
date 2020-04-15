import functools
import os
import signal
import re
from zipfile import ZipFile

from flask import current_app
from PIL import Image

from .database import db, Scan, Page, Submission, Solution, Student
from . import celery


RE_FILENAME = re.compile(r'(?P<studentID>\d{7})-(?P<page>\d+)-?(?P<copy>\d+)?\.(?P<ext>\w+)$')

EXIF_METHODS = {
    2: Image.FLIP_LEFT_RIGHT,
    3: Image.ROTATE_180,
    4: Image.FLIP_TOP_BOTTOM,
    5: Image.TRANSPOSE,
    6: Image.ROTATE_270,
    7: Image.TRANSVERSE,
    8: Image.ROTATE_90,
}


@celery.task()
def process_zipped_images(scan_id):
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
        _process_zipped_images(scan_id)
    except BaseException as error:
        # TODO: When #182 is implemented, properly separate user-facing
        #       messages (written to DB) from developer-facing messages,
        #       which should be written into the log.
        write_pdf_status(scan_id, 'error', "Unexpected error: " + str(error))


def _process_zipped_images(scan_id):
    data_directory = current_app.config['DATA_DIRECTORY']

    report_error = functools.partial(write_pdf_status, scan_id, 'error')
    report_progress = functools.partial(write_pdf_status, scan_id, 'processing')
    report_success = functools.partial(write_pdf_status, scan_id, 'success')

    # Raises exception if zero or more than one scans found
    scan = Scan.query.filter(Scan.id == scan_id).one()
    exam = scan.exam

    report_progress('Importing ZIP')

    zip_path = os.path.join(data_directory, 'scans', f'{scan.id}.zip')
    output_directory = os.path.join(data_directory, f'{exam.id}_data', 'submissions')

    with ZipFile(zip_path) as zip:
        total = sum(not zip_info.is_dir() for zip_info in zip.infolist())

    failures = []
    try:
        for number, (file_name, image) in enumerate(extract_images(zip_path)):
            report_progress(f'Processing file {number + 1} / {total}')
            try:
                success, description = process_page(
                    file_name, image, exam, output_directory
                )
                if not success:
                    print(description)
                    failures.append(f'{file_name}: {description}')
            except Exception as e:
                report_error(f'Error processing {file_name}: {e}')
                return
    except Exception as e:
        report_error(f"Failed to read zip: {e}")
        raise

    if failures:
        processed = total - len(failures)
        if processed:
            report_error(
                f'Processed {processed} / {total} files.\n'
                f'Failed on files:\n'
                + '\n'.join(failures)
            )
        else:
            report_error(f'Failed on all {total} files.\n'
                         + '\n'.join(failures))
    else:
        report_success(f'Processed {total} files.')


def extract_images(zip_path):
    with ZipFile(zip_path) as zip:
        for file_info in zip.infolist():
            if not file_info.is_dir():
                with zip.open(file_info.filename, mode='r') as f:
                    yield file_info.filename, f


def process_page(file_name, image, exam, output_directory):
    # Zip file names always have / as path separator
    file_name_without_dir = file_name.rsplit('/', 1)[-1]
    m = RE_FILENAME.match(file_name_without_dir)

    if not m:
        return False, f'Invalid file name (studentid-page.extension)'

    student_id = int(m.group('studentID'))
    page = int(m.group('page')) - 1
    copy = int(m.group('copy')) if m.group('copy') else 1

    student = Student.query.get(student_id)
    if not student:
        return False, f'Student number {student_id} not in the database'

    sub = retrieve_submission(exam, student_id, page, copy)

    os.makedirs(os.path.join(output_directory, f'{sub.copy_number}'), exist_ok=True)
    path = os.path.join(output_directory, f'{sub.copy_number}', f'page{page:02d}.jpg')

    try:
        save_image(image, path)
    except Exception as e:
        return False, f'File is not an image: ' + str(e)

    db.session.add(Page(path=os.path.relpath(path, start=current_app.config['DATA_DIRECTORY']),
                        submission=sub,
                        number=page))
    db.session.commit()

    return True, 'success'


def retrieve_submission(exam, student_id, page, copy):
    subs = Submission.query.filter(Submission.exam_id == exam.id, Submission.student_id == student_id)\
                           .order_by(Submission.copy_number.asc())\
                           .all()

    if len(subs) < copy:
        copy_num = next_free_copy_number(exam.id)
        for k in range(copy - len(subs)):
            sub = create_submission(copy_num + k, exam, student_id)

        return sub
    else:
        return subs[copy - 1]


def create_submission(copy_num, exam, student_id):
    sub = Submission(copy_number=copy_num, exam=exam, student_id=student_id)
    db.session.add(sub)

    for problem in exam.problems:
        db.session.add(Solution(problem=problem, submission=sub))

    return sub


def next_free_copy_number(exam_id):
    sub = Submission.query.filter(Submission.exam_id == exam_id)\
                          .order_by(Submission.copy_number.desc())\
                          .first()
    return sub.copy_number + 1 if sub else 1


def save_image(image, path):
    with Image.open(image) as original:
        rotated = exif_transpose(original)  # raises some error
        rotated.save(path)


def exif_transpose(image):
    """
    If an image has an EXIF Orientation tag, return a new image that is
    transposed accordingly.

    Adapted from PIL.ImageOps.exif_transpose.
    """
    exif = image._getexif()
    orientation = exif.get(0x0112)
    method = EXIF_METHODS.get(orientation)

    return image if not method else image.transpose(method)


def write_pdf_status(scan_id, status, message):
    scan = Scan.query.get(scan_id)
    scan.status = status
    scan.message = message
    db.session.commit()
