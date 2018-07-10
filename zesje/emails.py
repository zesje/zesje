from io import BytesIO

import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

import jinja2
from wand.image import Image
from pony import orm

from .database import Submission
from . import statistics


def solution_pdf(exam_id, student_id):
    with orm.db_session:
        subs = Submission.select(
            lambda s: s.exam.id == exam_id and s.student.id == student_id
        )
        pages = sorted((p for s in subs for p in s.pages), key=(lambda p: p.number))
        pages = [p.path for p in pages]

    with Image() as output_pdf:
        for filepath in pages:
            with Image(filename=filepath) as page:
                output_pdf.sequence.append(page)

        output_pdf.format = 'pdf'

        result = BytesIO()

        output_pdf.save(file=result)

    result.seek(0)

    return result


def form_email(exam_id, student_id, template, attach=True,
               text_only=True, subject='Your results',
               email_from='no-reply@tudelft.nl'):
    template = jinja2.Template(template)

    student, results = statistics.solution_data(exam_id, student_id)
    text = template.render(student=student, results=results)
    if text_only:
        return text

    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = email_from
    msg['To'] = student['email']
    msg['Reply-to'] = email_from
    msg.attach(MIMEText(text, 'plain'))

    if attach:
        solution = solution_pdf(exam_id, student_id)
        maintype, subtype = 'application', 'pdf'
        pdf = MIMEBase(maintype, subtype)
        pdf.set_payload(solution.read())
        encoders.encode_base64(pdf)
        # Set the filename parameter
        pdf.add_header('Content-Disposition', 'attachment',
                       filename=f"{student_id}.pdf")
        msg.attach(pdf)
    return msg


def send(messages):
    """Send a list of messages.

    returns the sequential numbers of messages that were not sent.
    """
    failed = []
    with smtplib.SMTP('dutmail.tudelft.nl', 25) as s:
        for number, msg in enumerate(messages):
            try:
                s.sendmail('noreply@tudelft.nl', [msg['To']], msg.as_string())
            except smtplib.SMTPException:
                failed.append(number)
    return failed
