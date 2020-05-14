import pytest
import zipfile

from io import BytesIO
from PIL import Image

from zesje.database import db, Exam, Student
from zesje.raw_scans import process_zipped_images


@pytest.fixture
def app_with_data(app):
    exam = Exam(name='', finalized=True)
    students = [Student(id=i+1000000, first_name='', last_name='') for i in range(2)]
    db.session.add(exam)
    for student in students:
        db.session.add(student)
    db.session.commit()
    yield app, exam, students


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


def test_no_zip(test_client, app_with_data, image_file):
    app, exam, students = app_with_data
    data = {
        'file': (image_file, 'image.jpg')
    }
    response = test_client.post(
        f'api/scans/raw/{exam.id}', data=data,
        content_type='multipart/form-data'
    )
    assert response.status_code == 400


def test_no_exam(test_client, zip_file):
    data = {
        'file': (zip_file, 'file.zip')
    }
    response = test_client.post(
        'api/scans/raw/1', data=data,
        content_type='multipart/form-data'
    )
    assert response.status_code == 404


def test_not_finalized_exam(test_client, zip_file, app_with_data):
    app, exam, students = app_with_data
    exam.finalized = False
    db.session.commit()

    data = {
        'file': (zip_file, 'file.zip')
    }
    response = test_client.post(
        f'api/scans/raw/{exam.id}', data=data,
        content_type='multipart/form-data'
    )
    assert response.status_code == 403


def test_processing_started(test_client, zip_file, app_with_data, monkeypatch):
    app, exam, students = app_with_data

    data = {
        'file': (zip_file, 'file.zip')
    }

    scan_ids = []
    monkeypatch.setattr(process_zipped_images, 'delay', lambda scan_id: scan_ids.append(scan_id))

    response = test_client.post(
        f'api/scans/raw/{exam.id}', data=data,
        content_type='multipart/form-data'
    )
    assert response.status_code == 200

    data = response.get_json()
    assert len(scan_ids) == 1
    assert scan_ids[0] == data['id']
