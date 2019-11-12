from io import BytesIO

import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

import jinja2

from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import cv2
from PIL import Image

from .database import Submission
from . import statistics
from .api.exams import PAGE_FORMATS
from .images import guess_dpi
from .api.images import _grey_out_student_widget
from .scans import exam_student_id_widget


def solution_pdf(exam_id, student_id, anonymous=False):
    """Send a dict of messages

    Parameters
    ----------
    exam_id : int
    student_id : int
    anonymous : bool, optional
        whether the pdfs and filenames need to be anonymized

    Returns
    -------
    result : BytesIO
        the students solution in pdf format.
    """
    subs = Submission.query.filter(Submission.exam_id == exam_id,
                                   Submission.student_id == student_id).all()
    pages = sorted((p for s in subs for p in s.pages), key=(lambda p: (p.submission.copy_number, p.number)))

    from flask import current_app
    page_format = current_app.config.get('PAGE_FORMAT', 'A4')  # TODO Remove default value
    page_size = PAGE_FORMATS[page_format]

    result = BytesIO()
    pdf = canvas.Canvas(result, pagesize=page_size)
    for page in pages:
        if anonymous and page.number == 0:
            page_im = cv2.imread(page.path)

            dpi = guess_dpi(page_im)

            # gray out student name and id
            student_id_widget, coords = exam_student_id_widget(exam_id)
            page_im = _grey_out_student_widget(page_im, coords, dpi)

            # convert cv2 image to pil image
            page_im = cv2.cvtColor(page_im, cv2.COLOR_BGR2RGB)
            pil_im = Image.fromarray(page_im)

            image = ImageReader(pil_im)
        else:
            image = page.path

        pdf.drawImage(image, 0, 0, width=page_size[0], height=page_size[1])
        pdf.showPage()

    pdf.save()
    result.seek(0)

    return result


def render(exam_id, student_id, template):
    template = jinja2.Template(template)
    student, results = statistics.solution_data(exam_id, student_id)
    return template.render(student=student, results=results)


def build_solution_attachment(exam_id, student_id):
    solution = solution_pdf(exam_id, student_id)
    maintype, subtype = 'application', 'pdf'
    pdf = MIMEBase(maintype, subtype)
    pdf.set_payload(solution.read())
    encoders.encode_base64(pdf)
    # Set the filename parameter
    pdf.add_header('Content-Disposition', 'attachment',
                   filename=f"{student_id}.pdf")
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


def send(
    messages,
    from_address,
    server, port=0, user=None, password=None, use_ssl=None,
):
    """Send a dict of messages

    Parameters
    ----------
    messages : dictionary
        A dict where the values are the messages to send, and
        the keys are unique message identifiers.
    server : string
        SMTP server domain name or IP address.
    port : int, optional
        STMP port.
    user, password : string, optional
        Login credentials.
    use_ssl : bool or None
        Whether to use SSL connection. If not provided, it is inferred from the
        port.

    Returns a list of the identifiers for messages that failed to send.
    """
    failed = []
    if use_ssl is None:
        use_ssl = port == 465
    server_type = smtplib.SMTP_SSL if use_ssl else smtplib.SMTP
    with server_type(server, port) as s:
        if user and password:
            s.login(user, password)
        for identifier, message in messages.items():
            recipients = [
                *message['To'].split(','),
                *(message['Cc'].split(',') if 'Cc' in message else [])
            ]
            try:
                s.sendmail(
                    from_address,
                    recipients,
                    message.as_string()
                )
            except smtplib.SMTPException:
                failed.append(identifier)
    return failed
