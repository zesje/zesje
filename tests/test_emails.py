import pytest
import os

from pikepdf import Pdf
import numpy as np

from zesje.database import db, Exam, ExamLayout, ExamWidget, Submission, Copy, Page, Student
from zesje.emails import solution_pdf, build, build_and_send, current_email_manager, _EmailManager
from zesje.api.emails import default_email_template
from zesje.image_extraction import extract_image_pikepdf
from zesje.images import get_box
from zesje.scans import exam_student_id_widget


def add_test_data(layout, data_dir):
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

    sub = Submission(exam=exam, student=student, validated=True)
    db.session.add(sub)

    copy = Copy(submission=sub, number=1)
    db.session.add(copy)

    for index, filepath in enumerate(['studentnumbers/1234323.jpg', 'studentnumbers/4300947.jpg']):
        page = Page(number=index, path=os.path.join(data_dir, filepath))
        db.session.add(page)
        copy.pages.append(page)
    db.session.commit()

    return exam, student


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


def test_defaul_email_manager(app):
    manager = current_email_manager()

    assert manager.hostname == app.config['SMTP_SERVER']
    assert manager.port == app.config['SMTP_PORT']
    assert manager.use_ssl == app.config['USE_SSL']
    assert manager.user == app.config['SMTP_USERNAME']
    assert manager.password == app.config['SMTP_PASSWORD']


def test_email_manager_reconnect(app, smtpd):
    manager = _EmailManager(
        hostname=smtpd.hostname,
        use_ssl=False,
        port=smtpd.port,
        user=app.config.get('SMTP_USERNAME'),
        password=app.config.get('SMTP_PASSWORD')
    )

    with manager as server:
        assert server.is_connected()

        server.server.close()
        assert not server.is_connected()

        server.reconnect()
        assert server.is_connected()

    assert not server.is_connected()


@pytest.mark.parametrize('attach', [True, False])
def test_build_and_send(app, smtpd, datadir, attach):
    manager = _EmailManager(
        hostname=smtpd.hostname,
        use_ssl=False,
        port=smtpd.port,
        user=app.config.get('SMTP_USERNAME'),
        password=app.config.get('SMTP_PASSWORD')
    )
    exam, student = add_test_data(ExamLayout.templated, datadir)

    sent, failed = build_and_send(
        [student], 'marks@teacher.com', exam, default_email_template, attach, _email_manager=manager
    )

    assert len(sent) == len(smtpd.messages) == 1
    assert sent[0] == student.id


class _DisconnectedManager(_EmailManager):
    """dummy server that does not connect automatically"""
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
