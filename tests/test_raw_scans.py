import pytest
import zipfile

from io import BytesIO
from PIL import Image
from pathlib import Path

from zesje.raw_scans import extract_image_info, create_copy, _process_zipped_images
from zesje.database import db, Exam, Student, Submission, Scan, Problem


@pytest.fixture
def app_with_data(app):
    exam = Exam(name='')
    problem = Problem(exam=exam, name='Problem')
    students = [Student(id=i+1000000, first_name='', last_name='') for i in range(2)]
    db.session.add(exam)
    db.session.add(problem)
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


@pytest.fixture
def image_file():
    with BytesIO() as image_bytes:
        image = Image.new('RGB', (10, 10))
        image.save(image_bytes, format='PNG')
        yield image_bytes


@pytest.fixture
def zip_file(image_file):
    with BytesIO() as zip_bytes:
        with zipfile.ZipFile(zip_bytes, 'w') as z:
            z.writestr('1000000-1.png', image_file.getvalue())
            z.writestr('1000001-1.png', image_file.getvalue())

        zip_bytes.seek(0)
        yield zip_bytes


def test_zip_process(app_with_data, zip_file):
    app, exam, students = app_with_data
    scan = Scan(exam=exam, name='test.zip', status='processing')
    db.session.add(scan)
    db.session.commit()

    path = Path(app.config['SCAN_DIRECTORY']) / f'{scan.id}.zip'
    print(path)
    with open(str(path), 'wb') as file:
        file.write(zip_file.getvalue())

    _process_zipped_images(scan.id)

    for student in students:
        sub = Submission.query.filter(Submission.student == student,
                                      Submission.exam == exam).one()
        assert sub.validated
        assert len(sub.copies) == 1
        copy = sub.copies[0]

        assert len(copy.pages) == 1
        page = copy.pages[0]
        assert page.number == 0
