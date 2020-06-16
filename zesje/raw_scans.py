from flask import current_app
from pathlib import Path

from .database import db, Exam, Page, Submission, Solution, Student, Copy


def process_page(image, page_info, file_info, exam_config, output_directory):
    student_id, page, copy = page_info

    if not student_id:
        return False, 'Unable to determine student.'

    student = Student.query.get(student_id)
    if not student:
        return False, f'Student number {student_id} not in the database'

    if None in (page, copy):
        return False, 'Unable to unambiguously determine page and copy number.'

    exam = Exam.query.filter(Exam.token == exam_config.token).one()

    if max(problem.widget.page for problem in exam.problems) == 0 and any('.pdf' in info for info in file_info):
        # single paged exam, each page of the pdf is treated as a different copy instead of a different page
        # this ensures that in the frontend the images are concatenated vertically
        page, copy = copy - 1, page + 1

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
