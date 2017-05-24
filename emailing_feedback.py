from pony import orm
import jinja2
import db
import os
import mimetypes
import subprocess

import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# db.use_db()

messages = []
def form_email(exam_id, student_id, template, attach=True,
               text_only=True, subject='Your results',
               email_from='no-reply@tudelft.nl'):
    template = jinja2.Template(template)

    student, results, pages = db.solution_data(exam_id, student_id)
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
        filename = str(student_id) + '.pdf'
        subprocess.call(['convert', *pages, filename])
        ctype, encoding = mimetypes.guess_type(filename)
        if ctype is None or encoding is not None:
            ctype = 'application/octet-stream'
        maintype, subtype = ctype.split('/', 1)
        with open(filename, 'rb') as fp:
            pdf = MIMEBase(maintype, subtype)
            pdf.set_payload(fp.read())
        encoders.encode_base64(pdf)
        # Set the filename parameter
        pdf.add_header('Content-Disposition', 'attachment',
                       filename=filename)
        msg.attach(pdf)
        os.remove(filename)
    return msg


def send(messages, recipients=None):
    """Send a list of messages.

    returns the sequential numbers of messages that were not sent due to
    missing recipient email.
    """
    failed = []
    with smtplib.SMTP('dutmail.tudelft.nl', 25) as s:
        for number, msg in enumerate(messages):
            to = recipients or [msg['To']]
            try:
                s.sendmail('noreply@tudelft.nl', to, msg.as_string())
            except smtplib.SMTPException:
                failed.append(number)
    return failed
