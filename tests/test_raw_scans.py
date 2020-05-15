import pytest
import zipfile

from io import BytesIO
from PIL import Image

from zesje.raw_scans import extract_page_info, create_copy, process_page
from zesje.scans import _process_scan
from zesje.database import db, Exam, Student, Submission, Scan, Problem, ExamWidget


@pytest.fixture
def app_with_data(app):
    exam = Exam(name='')
    widget = ExamWidget(name='barcode_widget', exam=exam, x=0, y=0)
    problem = Problem(exam=exam, name='Problem')
    students = [Student(id=i+1000000, first_name='', last_name='') for i in range(2)]
    db.session.add(exam)
    db.session.add(widget)
    db.session.add(problem)
    for student in students:
        db.session.add(student)
    db.session.commit()
    yield app, exam, students


@pytest.mark.parametrize('file_info, info', [
    (['1234567-02.png'], (1234567, 1, 1)),
    (['1234567-1-4.jpeg'], (1234567, 0, 4)),
    (['1234567.png'], None),
    (['ABCDEFG.jpeg'], None),
    (['1234567.zip', '1.pdf'], (1234567, 0, 1)),
    (['1234567.zip', '1-2.img'], (1234567, 0, 2)),
    (['1234567.pdf', 1], (1234567, 0, 1)),
    (['some.zip', '1234567.pdf', 1], (1234567, 0, 1)),
    (['some.zip', '1234567/2.pdf', 2], (1234567, 1, 2)),
    (['some.zip', '1234567-1.jpg'], (1234567, 0, 1)),
    (['some.zip', '1234567/1.png'], (1234567, 0, 1))],
    ids=[
    'Valid name (no copy)',
    'Valid name (with copy)',
    'Invalid name (no page)',
    'Invalid name (no student)',
    'Valid name (pdf page in zip)',
    'Valid name (with copy, img in zip)',
    'Valid name (pdf)',
    'Valid name (pdf in zip)',
    'Valid name (copy in pdf in zip)',
    'Valid name (img page in zip)',
    'Valid name (img in folder in zip'])
def test_extract_image_info(file_info, info):
    try:
        ext_info = extract_page_info(file_info)
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

    with open(str(scan.path), 'wb') as file:
        file.write(zip_file.getvalue())

    _process_scan(scan.id, process_page)

    for student in students:
        sub = Submission.query.filter(Submission.student == student,
                                      Submission.exam == exam).one()
        assert sub.validated
        assert len(sub.copies) == 1
        copy = sub.copies[0]

        assert len(copy.pages) == 1
        page = copy.pages[0]
        assert page.number == 0
