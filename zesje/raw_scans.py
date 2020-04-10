import functools
import os
import signal
import re
from zipfile import ZipFile

from flask import current_app

from .database import db, Scan, Page, Submission, Solution, Student
from . import celery


RE_FILENAME = re.compile(r'(?P<studentID>\d{7})-(?P<page>\d+)-?(?P<copy>\d+)?\.\w+$')


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

    report_progress('Importing PDF')

    zip_path = os.path.join(data_directory, 'scans', f'{scan.id}.zip')
    output_directory = os.path.join(data_directory, f'{exam.id}_data', 'submissions')

    with ZipFile(zip_path) as zip:
        total = len(zip.namelist())

    failures = []
    copy_num = 1  # the next copy number to be used
    try:
        for file_name, file in extract_images(zip_path):
            report_progress(f'Processing file {file_name}')
            try:
                success, description, copy_num = process_page(
                    file_name, file, exam, copy_num, output_directory
                )
                if not success:
                    print(description)
                    failures.append(description)
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
                f'Processed {processed} / {total} files. '
                f'Failed on files:\n'
                + '\n'.join(failures)
            )
        else:
            report_error(f'Failed on all {total} files.' + '\n'.join(failures))
    else:
        report_success(f'Processed {total} files.')


def extract_images(zip_path):
    with ZipFile(zip_path) as zip:
        for file_name in zip.namelist():
            with zip.open(file_name, mode='r') as f:
                yield file_name, f


def process_page(file_name, file, exam, copy_num, output_directory):
    m = RE_FILENAME.match(file_name)

    if not m:
        return False, f'File name "{file_name}" is not valid.', copy_num

    student_id = int(m.group('studentID'))
    page = int(m.group('page')) - 1

    student = Student.query.get(student_id)
    if not student:
        return False, f'Student number {student_id} not in the database', copy_num

    subs = Submission.query.filter(Submission.exam_id == exam.id, Submission.student_id == student_id).all()
    if not subs:
        sub = create_submission(copy_num, exam, student_id)
        copy_num += 1
    else:
        sub = get_submission_without_page(subs, page)
        if not sub:
            sub = create_submission(copy_num, exam, student_id)
            copy_num += 1

    os.makedirs(os.path.join(output_directory, f'{sub.copy_number}'), exist_ok=True)
    path = os.path.join(output_directory, f'{sub.copy_number}', f'page{page:02d}.jpg')

    with open(path, 'w+b') as out:
        out.write(file.read())

    db.session.add(Page(path=os.path.relpath(path, start=current_app.config['DATA_DIRECTORY']),
                        submission=sub,
                        number=page))
    db.session.commit()

    return True, 'success', copy_num


def create_submission(copy_num, exam, student_id):
    sub = Submission(copy_number=copy_num, exam=exam, student_id=student_id)
    db.session.add(sub)

    for problem in exam.problems:
        db.session.add(Solution(problem=problem, submission=sub))

    return sub


def get_submission_without_page(subs, page):
    for sub in subs:
        if not any(p.number == page for p in sub.pages):
            return sub

    return None


def write_pdf_status(scan_id, status, message):
    scan = Scan.query.get(scan_id)
    scan.status = status
    scan.message = message
    db.session.commit()
