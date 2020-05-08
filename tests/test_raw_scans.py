import pytest


from zesje.raw_scans import extract_image_info, create_copy
from zesje.database import db, Exam, Student, Submission


@pytest.fixture
def app_with_data(app):
    exam = Exam(name='')
    students = [Student(id=i+1, first_name='', last_name='') for i in range(2)]
    db.session.add(exam)
    for student in students:
        db.session.add(student)
    db.session.commit()
    yield app, exam, students


@pytest.mark.parametrize('file_name, info', [
    ('1234567-02.png', (1234567, 1, 1)),
    ('1234567-1-4.jpeg', (1234567, 0, 4)),
    ('1234567.png', None),
    ('ABCDEFG.jpeg', None)],
    ids=[
    'Valid name (no copy)',
    'Valid name (with copy)',
    'Invalid name (no page)',
    'Invalid name (no student)'])
def test_extract_image_info(file_name, info):
    try:
        ext_info = extract_image_info(file_name)
    except Exception:
        ext_info = None

    assert ext_info == info


def test_create_copy(app_with_data):
    app, exam, students = app_with_data
    submission = Submission(exam=exam, student=students[0])
    copy = create_copy(submission)

    assert copy.id == copy.number
