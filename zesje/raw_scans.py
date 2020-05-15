import re

from flask import current_app
from pathlib import Path

from .database import db, Exam, Page, Submission, Solution, Student, Copy
from .constants import ID_GRID_DIGITS


RE_STUDENT_PAGE = re.compile(
    fr'(?P<studentID>\d{{{ID_GRID_DIGITS}}})(-|\/)(?P<page>\d+)-?(?P<copy>\d+)?\.(?P<ext>\w+)$'
)
RE_COPY_OR_PAGE = re.compile(
    r'(?P<copy_or_page>\d+)$'
)
RE_PAGE = re.compile(
    r'(?P<page>\d+)-?(?P<copy>\d+)?(\.(?P<ext>\w+))?$'
)
RE_STUDENT = re.compile(
    fr'(?P<studentID>\d{{{ID_GRID_DIGITS}}})?\.(?P<ext>\w+)$'
)


def process_page(image, file_info, exam_config, output_directory):
    try:
        student_id, page, copy = extract_page_info(file_info)
    except Exception as e:
        return False, str(e)

    student = Student.query.get(student_id)
    if not student:
        return False, f'Student number {student_id} not in the database'

    exam = Exam.query.filter(Exam.token == exam_config.token).one()
    copy = retrieve_copy(exam, student_id, copy)

    image_dir = Path(output_directory) / 'submissions' / f'{copy.number}'
    image_dir.mkdir(exist_ok=True, parents=True)

    path = image_dir / f'page{page:02d}.jpg'

    image.save(path)

    db.session.add(Page(path=str(path.relative_to(current_app.config['DATA_DIRECTORY'])),
                        copy=copy,
                        number=page))
    db.session.commit()

    return True, 'success'


def extract_page_info(file_info):
    """Extract information about student, copy and page from the file name.

    Supports the following formats:
    - File of format student-page(-copy).ext
    - File in ZIP of format student/page(-copy).ext
    - File of format page(-copy).ext in a ZIP, parent should be student.ext
    - Page in a PDF, parent path should be student.pdf, student-page.pdf or student/page.pdf

    Params
    ------
    file_info : list of str and int
        See `image_extraction.extract_images_from_file`.

    Returns
    ------
    student_id : int
        Student number
    page : int
        Page number, 0-indexed
    copy : int
        Copy number, 1-indexed
    """
    filename = str(file_info[-1])

    # File of format student-page-copy.ext
    if (m := RE_STUDENT_PAGE.match(filename)):
        student_id = int(m.group('studentID'))
        page = int(m.group('page')) - 1
        copy = int(m.group('copy')) if m.group('copy') else 1

    # Page in a PDF, parent should be student.pdf, student-page.pdf student/page.pdf
    elif (match_copy_or_page := RE_COPY_OR_PAGE.match(filename)):
        copy_or_page = int(match_copy_or_page.group('copy_or_page'))

        if len(file_info) > 1 and (match := RE_STUDENT_PAGE.match(file_info[-2])):
            # Cannot specify copy for this format
            if match.group('copy'):
                raise ValueError('Invalid format, unable to determine student and page')

            student_id = int(match.group('studentID'))
            page = int(match.group('page')) - 1
            copy = copy_or_page
        elif len(file_info) > 1 and (match := RE_STUDENT.match(file_info[-2])):
            student_id = int(match.group('studentID'))
            page = copy_or_page - 1
            copy = 1

        else:
            raise ValueError('Invalid format, unable to determine student and page')

    # Page-copy.ext, parent should be student.ext
    elif (match_page := RE_PAGE.match(filename)):
        page = int(match_page.group('page')) - 1
        copy = int(match_page.group('copy')) if match_page.group('copy') else 1

        if len(file_info) > 1 and (match_student := RE_STUDENT.match(file_info[-2])):
            student_id = int(match_student.group('studentID'))
        else:
            raise ValueError('Invalid format, unable to determine student and page')

    else:
        raise ValueError('Invalid format, unable to determine student and page')

    return student_id, page, copy


def retrieve_copy(exam, student_id, copy):
    """Returns a copy associated the given student"""
    sub = Submission.query.filter(Submission.exam_id == exam.id, Submission.student_id == student_id)\
        .one_or_none()

    if not sub:
        sub = create_submission(exam, student_id, True)

    copies = sub.copies or []
    if len(copies) < copy:
        for k in range(copy - len(copies)):
            copy = create_copy(sub)
    else:
        copy = copies[copy - 1]

    return copy


def create_submission(exam, student_id, validated):
    """Adds a new submission to the db for the given exam and student"""
    sub = Submission(exam=exam, student_id=student_id, validated=validated)
    db.session.add(sub)

    for problem in exam.problems:
        db.session.add(Solution(problem=problem, submission=sub))

    return sub


def create_copy(sub):
    """Adds a new copy associated to the given submission whose number is equal to the id"""
    copy = Copy(submission=sub, number=0)
    db.session.add(copy)
    db.session.commit()
    copy.number = copy.id
    db.session.commit()

    return copy
