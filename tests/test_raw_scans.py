import pytest
import zipfile

from io import BytesIO
from PIL import Image
from pathlib import Path

from zesje.raw_scans import create_copy, process_page
from zesje.scans import _process_scan, exam_metadata
from zesje.database import db, Exam, Student, Submission, Scan, Problem, ProblemWidget, ExamLayout, Copy, Page


@pytest.fixture
def app_with_data(app):
    exam = Exam(name='', layout=ExamLayout.unstructured)
    problem = Problem(exam=exam, name='Problem')
    widget = ProblemWidget(problem=problem, x=0, y=0, width=0, height=0)
    students = [Student(id=i+1000000, first_name='', last_name='') for i in range(2)]
    db.session.add(exam)
    db.session.add(problem)
    db.session.add(widget)
    for student in students:
        db.session.add(student)
    db.session.commit()
    yield app, exam, students


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

    _process_scan(scan.id, exam.layout)

    for student in students:
        sub = Submission.query.filter(Submission.student == student,
                                      Submission.exam == exam).one()
        assert sub.validated
        assert len(sub.copies) == 1
        copy = sub.copies[0]

        assert len(copy.pages) == 1
        page = copy.pages[0]
        assert page.number == 0


def test_reupload_page(app_with_data, zip_file):
    app, exam, students = app_with_data
    student = students[0]
    file_name = 'old.txt'

    sub = Submission(exam=exam, student_id=student.id, validated=True)
    copy = Copy(submission=sub, number=1)
    page = Page(copy=copy, number=0, path=file_name)
    db.session.add_all([sub, copy, page])
    db.session.commit()

    old_path = Path(app.config['DATA_DIRECTORY']) / file_name
    old_path.write_text('old image data')

    image = Image.new('RGB', (10, 10))
    page_info = (student.id, page.number, copy.number)
    file_info = [f'{student.id}-{page.number+1}-{page.copy.number}.jpg']
    exam_config = exam_metadata(exam)
    output_directory = app.config['DATA_DIRECTORY']

    process_page(image, page_info, file_info, exam_config, output_directory)

    # Only a single page entry
    assert Page.query.filter(Page.copy == copy, Page.number == page.number).one()

    # Path was updated and only new image still exists
    assert page.path != file_name
    assert not old_path.exists()
    assert Path(page.abs_path).exists()
