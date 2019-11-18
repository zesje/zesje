""" REST api for email templates """
from pathlib import Path
import textwrap

from jinja2 import Template, TemplateSyntaxError, UndefinedError

import werkzeug.exceptions
from flask import current_app
from flask_restful import Resource, reqparse

from .. import emails
from ..database import Exam, Student
from ._helpers import abort

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


def build_email(exam_id, student_id, template, attach, from_address, copy_to=None):
    student = Student.query.get(student_id)
    if student is None:
        abort(
            404,
            message=f"Student #{student_id} does not exist"
        )
    if not student.email:
        abort(
            409,
            message=f'Student #{student_id} has no email address'
        )

    return emails.build(
        student.email,
        render_email(exam_id, student_id, template),
        emails.build_solution_attachment(exam_id, student_id)
        if attach
        else None,
        copy_to=copy_to,
        email_from=from_address,
    )


class EmailTemplate(Resource):
    """ Email template. """

    def get(self, exam_id):
        """Get an email template for a given exam."""
        try:
            with open(template_path(exam_id)) as f:
                return f.read()
        except FileNotFoundError:
            with open(template_path(exam_id), 'w') as f:
                f.write(default_email_template)
            return default_email_template

    put_parser = reqparse.RequestParser()
    put_parser.add_argument('template', type=str, required=True)

    def put(self, exam_id):
        """Update an email template."""
        email_template = self.put_parser.parse_args().template
        try:
            Template(email_template)
        except TemplateSyntaxError as error:
            return dict(
                status=400,
                message=f"Syntax error in the template: {error.message}"
            ), 400

        with open(template_path(exam_id), 'w') as f:
            f.write(email_template)


class RenderedEmailTemplate(Resource):

    post_parser = reqparse.RequestParser()
    post_parser.add_argument('template', type=str, required=True)

    def post(self, exam_id, student_id):
        template = self.post_parser.parse_args().template
        return render_email(exam_id, student_id, template)


class Email(Resource):

    post_parser = reqparse.RequestParser()
    post_parser.add_argument('template', type=str, required=True)
    post_parser.add_argument('attach', type=bool, required=True)
    post_parser.add_argument('copy_to', type=str, required=False)

    def post(self, exam_id, student_id=None):
        """Send an email.

        Returns
        -------
        400 error if not all submissions from exam are validated (because we
        might send wrong emails this way).
        """
        args = self.post_parser.parse_args()
        template = args['template']
        attach = args['attach']
        copy_to = args['copy_to']

        if student_id is None and copy_to is not None:
            abort(
                409,
                message="Not CC-ing all emails from the exam."
            )

        exam = Exam.query.get(exam_id)
        if exam is None:
            abort(
                404,
                message="Exam does not exist"
            )

        if not all(sub.signature_validated for sub in exam.submissions):
            abort(
                409,
                message="All submissions must be validated before "
                        "sending emails."
            )

        if student_id is not None:
            return self._send_single(exam_id, student_id, template, attach, copy_to)
        else:
            return self._send_all(exam_id, template, attach)

    def _send_single(self, exam_id, student_id, template, attach, copy_to):
        if not (current_app.config.get('SMTP_SERVER') and current_app.config.get('FROM_ADDRESS')):
            abort(
                500,
                message='Sending email is not configured'
            )
        message = build_email(
            exam_id, student_id, template,
            attach, current_app.config['FROM_ADDRESS'], copy_to,
        )
        failed = emails.send(
            {student_id: message},
            server=current_app.config['SMTP_SERVER'],
            from_address=current_app.config['FROM_ADDRESS'],
            port=current_app.config.get('SMTP_PORT'),
            user=current_app.config.get('SMTP_USERNAME'),
            password=current_app.config.get('SMTP_PASSWORD'),
            use_ssl=current_app.config.get('USE_SSL'),
        )
        if failed:
            abort(
                500,
                message=f'Failed to send email to student #{student_id}'
            )
        return dict(status=200)

    def _send_all(self, exam_id, template, attach):
        if not (current_app.config.get('SMTP_SERVER') and current_app.config.get('FROM_ADDRESS')):
            abort(
                500,
                message='Sending email is not configured'
            )
        exam = Exam.query.get(exam_id)
        if exam is None:
            abort(
                404,
                message="Exam does not exist"
            )
        student_ids = set(sub.student.id for sub in exam.submissions if sub.student)

        failed_to_build = list()
        to_send = dict()
        for student_id in student_ids:
            try:
                to_send[student_id] = build_email(
                    exam_id, student_id, template,
                    attach, current_app.config['FROM_ADDRESS'],
                )
            except werkzeug.exceptions.Conflict:
                # No email address provided. Any other failures are errors,
                # so we let other exceptions raise.
                failed_to_build.append(student_id)

        failed_to_send = emails.send(
            to_send,
            server=current_app.config['SMTP_SERVER'],
            from_address=current_app.config['FROM_ADDRESS'],
            port=current_app.config.get('SMTP_PORT'),
            user=current_app.config.get('SMTP_USERNAME'),
            password=current_app.config.get('SMTP_PASSWORD'),
            use_ssl=current_app.config.get('USE_SSL'),
        )

        sent = set(student_ids) - (set(failed_to_send) | set(failed_to_build))
        sent = list(sent)

        if failed_to_build or failed_to_send:
            if len(sent) > 0:
                return dict(
                    status=206,
                    message='Failed to send some emails',
                    sent=sent,
                    failed_to_build=failed_to_build,
                    failed_to_send=failed_to_send,
                ), 206
            elif not failed_to_send:  # all failed to build
                abort(
                    409,
                    message='No students have email addresses specified',
                ), 409
            elif not failed_to_build:  # all failed to send
                abort(
                    500,
                    message='Failed to send emails',
                    failed_to_send=failed_to_send,
                ), 500
            else:
                abort(
                    500,
                    message=(
                        f'Email addresses unspecified for {len(failed_to_build)} students '
                        f'and {len(failed_to_send)} messages failed to send.'
                    ),
                    failed_to_build=failed_to_build,
                    failed_to_send=failed_to_send,
                ), 500
        else:
            return dict(status=200)
