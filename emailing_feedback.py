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

default_template = jinja2.Template("""Dear {{student.first_name.split(' ') | first }} {{student.last_name}},

Below please find attached the scans of your exam and our feedback.
If you have any questions, don't hesitate to contant us during the exercise classes
or in the course chat https://chat.quantumtinkerer.tudelft.nl/solidstate

Additionally, you may want to compare your results with the overall performance
of your colleagues over here:
as well as a reference solution

{% for problem in results | sort(attribute='name') if problem.feedback  -%}
{{problem.name}} (your score: {{problem.score}} out of {{problem.max_score}}):
{% for feedback in problem.feedback %}
    * {{ (feedback.description or feedback.short) | wordwrap | indent(width=6) }}
{% endfor %}
{%- if problem.remarks %}
    * {{ problem.remarks | wordwrap | indent(width=6) }}
{% endif %}
{% endfor %}

{%- if student.total < 60 -%}
Your grade is below 6.
{%- elif student.total < 80 -%}
Your grade is between 6 and 8.
{%- else -%}
Your grade is above 8.
{%- endif%}

Best,
Solid state course team.
""")

default_template.trim_blocks = default_template.lstrip_blocks = True

messages = []
def form_email(submission_id, template=None, attach=True,
               text_only=True, subject='Your results',
               email_from='no-reply@tudelft.nl'):
    if template is None:
        template = default_template
    else:
        template = jinja2.Template(template)
    with orm.db_session:
        sub = db.Submission[submission_id]
        filename = '{}.pdf'.format(sub.student.id)
        pages = sorted(set(sub.pages.path))  # Hotfix for issue 50.
        results = [
         {'name': i.problem.name,
          'score': orm.sum(i.feedback.score),
          'max_score' : orm.max(i.problem.feedback_options.score, default=0),
          'feedback': [{'short': fo.text,
                        'score': fo.score,
                        'description': fo.description} for fo in i.feedback],
          'remarks': i.remarks,
         } for i in sub.solutions]

        student = sub.student.to_dict()
        email = sub.student.email

    student['total'] = sum(i['score'] for i in results)

    text = template.render(student=student, results=results)
    if text_only:
        return text

    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = email_from
    msg['To'] = email
    msg['Reply-to'] = email_from
    msg.attach(MIMEText(text, 'plain'))

    if attach:
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
    with smtplib.SMTP('dutmail.tudelft.nl', 25) as s:
        for number, msg in enumerate(messages):
            to = recipients or [msg['To']]
            s.sendmail('noreply@tudelft.nl', to, msg.as_string())
