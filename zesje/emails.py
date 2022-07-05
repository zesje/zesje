from io import BytesIO
from enum import Enum

import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

from jinja2 import Template, TemplateSyntaxError, UndefinedError
from flask import current_app
import werkzeug.exceptions

from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import cv2
from PIL import Image

from .database import Submission, ExamLayout
from . import statistics
from .images import guess_dpi
from .api.images import _grey_out_student_widget
from .scans import exam_student_id_widget


FailStatus = Enum(
    'FailStatus',
    'build attach send'
)


class _EmailManager():
    """Context email manager for sending emails logged in.

    This takes care of reconnecting to the server in case it disconnects which can happen
    when sending a lot of emails with relatively large idle time between them. For instance,
    when building the solution pdf.

    Parameters
    ----------
    server : string
        SMTP server domain name or IP address.
    use_ssl : bool or None
        Whether to use SSL connection. If not provided, it is inferred from the
        port.
    port : int, optional
        STMP port.
    user, password : string, optional
        Login credentials.
    """

    def __init__(self, server, use_ssl=None, port=465, user=None, password=None):
        self.server = server
        self.use_ssl = use_ssl
        self.port = port
        if self.use_ssl is None:
            self.use_ssl = self.port == 465
        self.server_type = smtplib.SMTP_SSL if self.use_ssl else smtplib.SMTP
        self.user = user
        self.password = password

    def __enter__(self):
        self.server = self.server_type(self.server, self.port)
        if self.port == 587:
            self.server.starttls()
        if self.user and self.password:
            self.server.login(self.user, self.password)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.server:
            self.server.__exit__()

    def reconnect(self):
        """reconnect to the server or raise an `SMTPConnectError`"""
        status, msg = self.server.connect(self.server, self.port)
        if status != 220:
            self.server.close()
            raise smtplib.SMTPConnectError(status, msg)

    def is_connected(self):
        # https://stackoverflow.com/questions/12552905/python-can-i-check-if-smtp-server-is-disconnected-so-i-can-connect-again
        try:
            status = self.server.noop()[0]
        except smtplib.SMTPServerDisconnected:
            status = -1

        return status == 250

    def send(self, from_address, message):
        """sends an email from `from_address` with content `message` but reconnects and tries again if disconnected."""
        try:
            recipients = [
                *message['To'].split(','),
                *(message['Cc'].split(',') if 'Cc' in message else [])
            ]

            self.server.sendmail(
                from_address,
                recipients,
                message.as_string()
            )
        except smtplib.SMTPServerDisconnected:
            # server has disconnected, try to reconnect and send the message again
            print('email server disconnected, trying to connect again.')
            self.reconnect()
            self.send(from_address, message)


def current_email_manager():
    return _EmailManager(
        server=current_app.config['SMTP_SERVER'],
        use_ssl=current_app.config.get('USE_SSL'),
        port=current_app.config.get('SMTP_PORT'),
        user=current_app.config.get('SMTP_USERNAME'),
        password=current_app.config.get('SMTP_PASSWORD')
    )


def solution_pdf(exam_id, student_id, anonymous=False):
    """Build a (anonymous) pdf from student's solution images of an exam.

    Parameters
    ----------
    exam_id : int
    student_id : int
    anonymous : bool, optional
        whether the solution images needs to be anonymized

    Returns
    -------
    result : BytesIO
        the student's solution in pdf format.
    """
    sub = Submission.query.filter(Submission.exam_id == exam_id,
                                  Submission.student_id == student_id,
                                  Submission.validated).one_or_none()
    if sub is None:
        raise RuntimeError('Student did not make a submission for this exam')

    pages = sorted((page for copy in sub.copies for page in copy.pages), key=(lambda p: (p.copy.number, p.number)))

    page_size = current_app.config['PAGE_FORMATS'][current_app.config['PAGE_FORMAT']]

    result = BytesIO()
    pdf = canvas.Canvas(result, pagesize=page_size)
    for page in pages:
        if anonymous and page.number == 0 and sub.exam.layout == ExamLayout.templated:
            page_im = cv2.imread(page.abs_path)

            dpi = guess_dpi(page_im)

            # gray out student name and id
            student_id_widget, coords = exam_student_id_widget(exam_id)
            page_im = _grey_out_student_widget(page_im, coords, dpi)

            # convert cv2 image to pil image
            page_im = cv2.cvtColor(page_im, cv2.COLOR_BGR2RGB)
            pil_im = Image.fromarray(page_im)

            image = ImageReader(pil_im)
        else:
            image = page.abs_path

        pdf.drawImage(image, 0, 0, width=page_size[0], height=page_size[1])
        pdf.showPage()

    pdf.save()
    result.seek(0)

    return result


def render(exam_id, student_id, template):
    template = Template(template)
    student, results = statistics.solution_data(exam_id, student_id)
    return template.render(student=student, results=results)


def build_solution_attachment(exam_id, student_id, file_name=None):
    solution = solution_pdf(exam_id, student_id)
    maintype, subtype = 'application', 'pdf'
    pdf = MIMEBase(maintype, subtype)
    pdf.set_payload(solution.read())
    encoders.encode_base64(pdf)

    if file_name is None:
        # construct the default filename if none is provided
        file_name = f"{student_id}.pdf"

    # Set the filename parameter
    pdf.add_header('Content-Disposition', 'attachment', filename=file_name)
    return pdf


def build(email_to, content, attachment=None, copy_to=None,
          subject='Your results',
          email_from='no-reply@tudelft.nl'):

    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = email_from
    msg['To'] = email_to
    if copy_to is not None:
        msg['Cc'] = copy_to
    msg['Reply-to'] = email_from
    msg.attach(MIMEText(content, 'plain'))

    if attachment:
        msg.attach(attachment)

    return msg


def build_and_send(
    students, from_address, exam, template, attach=False, copy_to=None
):
    """Build and send the student solution emails.

    Parameters
    ----------
    students : list of Student
        the students to send the emails to
    from_address : str
        the from email address
    exam : Exam
        the exam to send
    template : str
        the jinja2 template to send as email content
    attach : bool
        whether to attach the solution pdf (default to False)
    copy_to : str
        the CC email address

    Returns
    -------
    sent
        the list of of students id that where send
    failed
        dict of students that failed, including status and error message
    """
    failed = []
    sent = []

    with current_email_manager() as server:
        for student in students:
            try:
                attachment = build_solution_attachment(exam.id, student.id, file_name=f'{student.id}_{exam.name}.pdf')
                content = render(exam.id, student.id, template)
                message = build(
                    student.email,
                    content,
                    attachment if attach else None,
                    copy_to=copy_to,
                    email_from=from_address,
                )
                server.send(from_address, message)
            except TemplateSyntaxError as error:
                failed.append({
                    'studentID': student.id,
                    'status': FailStatus.build.name,
                    'message': f"Syntax error in the template: {error.message}"
                })
            except UndefinedError as error:
                failed.append({
                    'studentID': student.id,
                    'status': FailStatus.build.name,
                    'message': f"Undefined variables in the template: {error.message}"
                })
            except werkzeug.exceptions.Conflict as e:
                # No email address provided. Any other failures are errors,
                # so we let other exceptions raise.
                failed.append({
                    'studentID': student.id,
                    'status': FailStatus.build.name,
                    'message': f"No email address provided: {e.message}"
                })
            except smtplib.SMTPException as e:
                # see https://docs.python.org/3/library/smtplib.html?highlight=smtplib#smtplib.SMTP.sendmail
                failed.append({
                    'studentID': student.id,
                    'status': FailStatus.send.name,
                    'message': str(e)
                })
            except Exception as e:
                failed.append({
                    'studentID': student.id,
                    'status': FailStatus.attach.name,
                    'message': str(e)
                })
            else:
                sent.append(student.id)

    return sent, failed
