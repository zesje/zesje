import pytest
import zipfile

from io import BytesIO

from zesje.database import db, Exam, Scan, ExamLayout
from zesje.scans import process_scan


@pytest.fixture
def app_with_data(app):
    exam = Exam(name='', finalized=True, layout=ExamLayout.unstructured)
    db.session.add(exam)
    db.session.commit()
    yield app, exam


@pytest.fixture
def zip_file():
    with BytesIO() as zip_bytes:
        with zipfile.ZipFile(zip_bytes, 'w') as z:
            z.writestr('1000000-1.png', b'abc')

        zip_bytes.seek(0)
        yield zip_bytes


def test_no_zip(test_client, app_with_data):
    app, exam = app_with_data
    data = {
        'file': (b'abc', 'image.jpg')
    }
    response = test_client.post(
        f'api/scans/{exam.id}', data=data,
        content_type='multipart/form-data'
    )
    assert response.status_code == 422


def test_no_exam(test_client, zip_file):
    data = {
        'file': (zip_file, 'file.zip')
    }
    response = test_client.post(
        'api/scans/1', data=data,
        content_type='multipart/form-data'
    )
    assert response.status_code == 404


def test_not_finalized_exam(test_client, zip_file, app_with_data):
    app, exam = app_with_data
    exam.finalized = False
    db.session.commit()

    data = {
        'file': (zip_file, 'file.zip')
    }
    response = test_client.post(
        f'api/scans/{exam.id}', data=data,
        content_type='multipart/form-data'
    )
    assert response.status_code == 403


def test_saving_zip_failed(test_client, zip_file, app_with_data, monkeypatch):
    app, exam = app_with_data

    app_config_mock = app.config.copy()
    app_config_mock['SCAN_DIRECTORY'] = None
    monkeypatch.setattr(app, 'config', app_config_mock)

    data = {
        'file': (zip_file, 'file.zip')
    }
    response = test_client.post(
        f'api/scans/{exam.id}', data=data,
        content_type='multipart/form-data'
    )
    assert response.status_code == 500
    assert len(Scan.query.all()) == 0


def test_processing_started(test_client, zip_file, app_with_data, monkeypatch):
    app, exam = app_with_data

    data = {
        'file': (zip_file, 'file.zip')
    }

    scan_ids = []
    monkeypatch.setattr(process_scan, 'delay', lambda scan_id, scan_type: scan_ids.append(scan_id))

    response = test_client.post(
        f'api/scans/{exam.id}', data=data,
        content_type='multipart/form-data'
    )
    assert response.status_code == 200

    data = response.get_json()
    assert len(scan_ids) == 1
    assert scan_ids[0] == data['id']
