import pytest
import os

from pikepdf import Pdf
import numpy as np
import werkzeug
import smtplib

from zesje.database import db, Exam, ExamLayout, ExamWidget, Submission, Copy, Page, Student
from zesje.emails import solution_pdf, build, build_and_send, current_email_manager, _EmailManager
from zesje.api.emails import default_email_template
from zesje.image_extraction import extract_image_pikepdf
from zesje.images import get_box
from zesje.scans import exam_student_id_widget


def add_test_data(layout, data_dir, validated=True):
    exam = Exam(name='Email', layout=layout, finalized=True)
    student = Student(id=1234323, first_name='Jamy', last_name='Macgiver', email='J.M@tudelft.nl')
    db.session.add(exam)
    db.session.add(student)
    db.session.commit()

    if layout == ExamLayout.templated:
        db.session.add(ExamWidget(
            name='student_id_widget',
            x=50,
            y=50,
            exam=exam,
        ))
        db.session.commit()

    sub = Submission(exam=exam, student=student, validated=validated)
    db.session.add(sub)

    copy = Copy(submission=sub, number=1)
    db.session.add(copy)

    for index, filepath in enumerate(['studentnumbers/1234323.jpg', 'studentnumbers/4300947.jpg']):
        page = Page(number=index, path=os.path.join(data_dir, filepath))
        db.session.add(page)
        copy.pages.append(page)
    db.session.commit()

    return exam, student


@pytest.fixture
def email_app(app, smtpd):
    app.config['SMTP_SERVER'] = smtpd.hostname
    app.config['SMTP_PORT'] = smtpd.port

    yield app


@pytest.fixture
def email_client(email_app):
    with email_app.test_client() as client:
        yield client


@pytest.mark.parametrize('layout, anonymous', [
    (ExamLayout.templated, False),
    (ExamLayout.templated, True),
    (ExamLayout.unstructured, False),
    (ExamLayout.unstructured, True)
], ids=['Templated', 'Templated & anonymous', 'Unstructured', 'Unstructured & anonymous'])
def test_solution_pdf(app, datadir, layout, anonymous):
    exam, student = add_test_data(layout, datadir)

    with Pdf.open(solution_pdf(exam.id, student.id, anonymous=anonymous)) as pdf:
        pagecount = len(pdf.pages)
        assert pagecount == 2

        if anonymous and layout == ExamLayout.templated:
            image = extract_image_pikepdf(pdf.pages[0])
            _, coords = exam_student_id_widget(exam.id)
            widget_area = get_box(np.array(image), np.array(coords, dtype=float) / 72, padding=-.3)
            w, h, *_ = widget_area.shape

            assert 145 < (np.mean(widget_area[:w//2]) + np.mean(widget_area[:, :h//2])) / 2 < 155


def test_build_email():
    message = build(
        'alice@quantum.com',
        'This is your key...',
        attachment=False,
        copy_to='charlie@quantum.com',
        subject='Secret key',
        email_from='bob@quantum.com'
    )

    assert message['From'] == 'bob@quantum.com'
    assert message['To'] == 'alice@quantum.com'
    assert message['Cc'] == 'charlie@quantum.com'
    assert message['Subject'] == 'Secret key'


def test_defaul_email_manager(email_app):
    manager = current_email_manager()

    assert manager.hostname == email_app.config['SMTP_SERVER']
    assert manager.port == email_app.config['SMTP_PORT']
    assert manager.use_ssl == email_app.config['USE_SSL']
    assert manager.user == email_app.config['SMTP_USERNAME']
    assert manager.password == email_app.config['SMTP_PASSWORD']


def test_email_manager_reconnect(email_app):
    manager = current_email_manager()

    with manager as server:
        assert server.is_connected()

        server.server.close()
        assert not server.is_connected()

        server.reconnect()
        assert server.is_connected()

    assert not server.is_connected()


@pytest.mark.parametrize('attach', [True, False])
def test_build_and_send(email_app, smtpd, datadir, attach):
    exam, student = add_test_data(ExamLayout.templated, datadir)

    sent, failed = build_and_send(
        [student], 'marks@teacher.com', exam, default_email_template, attach
    )

    assert len(sent) == len(smtpd.messages) == 1
    assert sent[0] == student.id


class _DisconnectedManager(_EmailManager):
    """dummy server that counts the number of reconnects"""
    reconnects = 0

    def __enter__(self):
        super().__enter__()
        self.server.__exit__()
        return self

    def reconnect(self):
        super().reconnect()
        self.reconnects += 1


def test_send_after_disconnect(app, smtpd, datadir):
    manager = _DisconnectedManager(
        hostname=smtpd.hostname,
        use_ssl=False,
        port=smtpd.port,
        user=app.config.get('SMTP_USERNAME'),
        password=app.config.get('SMTP_PASSWORD')
    )
    exam, student = add_test_data(ExamLayout.templated, datadir)

    sent, failed = build_and_send(
        [student], 'marks@teacher.com', exam, default_email_template, attach=False, _email_manager=manager
    )

    assert manager.reconnects == 1

    assert len(sent) == len(smtpd.messages) == 1
    assert sent[0] == student.id


@pytest.mark.parametrize('all', [True, False])
def test_api(email_client, datadir, all):
    exam, student = add_test_data(ExamLayout.templated, datadir)

    result = email_client.post(
        f'/api/email/{exam.id}' if all else f'/api/email/{exam.id}/{student.id}',
        data={'template': default_email_template, 'attach': False}
    )

    assert result.status_code == 200


def test_copy_to_without_student(email_client, datadir):
    exam, student = add_test_data(ExamLayout.templated, datadir)

    result = email_client.post(
        f'/api/email/{exam.id}',
        data={'template': default_email_template, 'attach': False, 'copy_to': 'john.doe@unknown'}
    )

    assert result.status_code == 409


def test_submission_not_validated(email_client, datadir):
    exam, student = add_test_data(ExamLayout.templated, datadir, validated=False)

    result = email_client.post(
        f'/api/email/{exam.id}',
        data={'template': default_email_template, 'attach': False}
    )

    assert result.status_code == 409


class _RaiseManager(_EmailManager):
    """dummy server that counts the number of reconnects"""
    def __init__(self, error, **kwargs):
        super().__init__(**kwargs)
        self.error = error

    def send(self, from_address, message):
        raise self.error


@pytest.mark.parametrize('error, status', [
    (werkzeug.exceptions.Conflict(), 'build'),
    (smtplib.SMTPRecipientsRefused({'J.M@tudelft.nl': (666, b'devil')}), 'send'),
    (smtplib.SMTPResponseException(666, b'devil'), 'send'),
    (RuntimeError, 'attach')
])
def test_server_error(app, smtpd, datadir, error, status):
    exam, student = add_test_data(ExamLayout.templated, datadir)

    manager = _RaiseManager(
        error=error,
        hostname=smtpd.hostname,
        use_ssl=False,
        port=smtpd.port,
        user=app.config.get('SMTP_USERNAME'),
        password=app.config.get('SMTP_PASSWORD')
    )

    sent, failed = build_and_send(
        [student], 'marks@teacher.com', exam, default_email_template, attach=False, _email_manager=manager
    )

    assert len(failed) == 1
    assert failed[0]['status'] == status


def test_server_not_configured(email_client, email_app, datadir):
    exam, student = add_test_data(ExamLayout.templated, datadir)

    email_app.config['SMTP_SERVER'] = None
    email_app.config['FROM_ADDRESS'] = None

    result = email_client.post(
        f'/api/email/{exam.id}',
        data={'template': default_email_template, 'attach': False}
    )

    assert result.status_code == 409
