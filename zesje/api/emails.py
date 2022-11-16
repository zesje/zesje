""" REST api for email templates """
from pathlib import Path
import textwrap

from jinja2 import Template, TemplateSyntaxError, UndefinedError

from flask import current_app
from flask.views import MethodView
from webargs import fields, validate

from ._helpers import DBModel, use_args, use_kwargs, abort
from .. import emails
from ..database import Exam, Student

default_email_template = str.strip(textwrap.dedent("""
    Dear {{student.first_name.split(' ') | first }} {{student.last_name}},

    Below please find attached the scans of your exam and our feedback.
    If you have any questions, don't hesitate to contact us.

    {% for problem in results | sort(attribute='name') if problem.feedback  -%}
    {{problem.name}} (your score: {{problem.score}} out of {{problem.max_score}}):
    {% for feedback in problem.feedback %}
        * {{ (feedback.description or feedback.short) | wordwrap | indent(width=6) }}
    {% endfor %}
    {%- if problem.remarks %}
        * {{ problem.remarks | wordwrap | indent(width=6) }}
    {% endif %}
    {% endfor %}

    Therefore your grade is {{ student.total }}.

    Best regards,
    Course team.
"""))


def template_path(exam_id):
    data_dir = Path(current_app.config['DATA_DIRECTORY'])
    template_file = data_dir / f'{exam_id}_data' / 'email_template.j2'
    return template_file


def render_email(exam_id, student_id, template):
    try:
        return emails.render(exam_id, student_id, template)
    except TemplateSyntaxError as error:
        abort(
            400,
            message=f"Syntax error in the template: {error.message}",
        )
    except UndefinedError as error:
        abort(
            400,
            message=f"Undefined variables in the template: {error.message}",
        )


class EmailTemplate(MethodView):
    """ Email template. """

    @use_kwargs({'exam': DBModel(Exam, required=True)})
    def get(self, exam):
        """Get an email template for a given exam."""
        try:
            with open(template_path(exam.id)) as f:
                return f.read()
        except FileNotFoundError:
            with open(template_path(exam.id), 'w') as f:
                f.write(default_email_template)
            return default_email_template

    @use_kwargs({'exam': DBModel(Exam, required=True)})
    @use_kwargs({"template": fields.Str(required=True)}, location="form")
    def put(self, exam, template):
        """Update an email template."""
        try:
            Template(template)
        except TemplateSyntaxError as error:
            return dict(
                status=400,
                message=f"Syntax error in the template: {error.message}"
            ), 400

        with open(template_path(exam.id), 'w') as f:
            f.write(template)

        return dict(status=200), 200


class RenderedEmailTemplate(MethodView):

    @use_kwargs({
        'exam': DBModel(Exam, required=True),
        'student': DBModel(Student, required=True)
    })
    @use_kwargs({"template": fields.Str(required=True)}, location="form")
    def post(self, exam, student, template):
        return render_email(exam.id, student.id, template)


class Email(MethodView):

    @use_kwargs({
        'exam': DBModel(Exam, required=True),
        'student': DBModel(Student, required=False, load_default=None)
    })
    @use_args({
        "template": fields.Str(required=True),
        'attach': fields.Bool(required=True),
        'copy_to': fields.Email(required=False, load_default=None)
    }, location="form")
    def post(self, args, exam, student):
        """Send an email.

        Returns
        -------
        400 error if not all submissions from exam are validated
        (because we might send wrong emails this way).
        """
        template = args['template']
        attach = args['attach']
        copy_to = args['copy_to']

        if student is None and copy_to is not None:
            return dict(
                status=409,
                message="Not CC-ing all emails from the exam."
            ), 409

        if not all(sub.validated for sub in exam.submissions):
            return dict(
                status=409,
                message="All copies must be validated before sending emails."
            ), 409

        if not (current_app.config.get('SMTP_SERVER') and current_app.config.get('FROM_ADDRESS')):
            return dict(
                status=409,
                message='Sending email is not configured'
            ), 409

        if student is not None:
            students = [student]
        else:
            students = [sub.student for sub in exam.submissions if sub.student_id and sub.validated]

        sent, failed = emails.build_and_send(
            students,
            from_address=current_app.config['FROM_ADDRESS'],
            exam=exam,
            template=template,
            attach=attach
        )

        if failed:
            if len(sent) > 0:
                return dict(
                    status=206,
                    message=f'Failed to send some emails ({len(sent)}/{len(students)}).',
                    sent=sent,
                    failed=failed
                ), 206
            else:
                return dict(
                    status=500,
                    message='Failed to send all emails.',
                    failed=failed,
                ), 500

        return dict(status=200), 200
