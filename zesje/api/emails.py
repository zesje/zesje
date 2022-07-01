""" REST api for email templates """
from pathlib import Path
import textwrap

from jinja2 import Template, TemplateSyntaxError, UndefinedError

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


class EmailTemplate(Resource):
    """ Email template. """

    def get(self, exam_id):
        """Get an email template for a given exam."""
        if not Exam.query.get(exam_id):
            return dict(status=404, message='Exam does not exist.'), 404

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
        if not Exam.query.get(exam_id):
            return dict(status=404, message='Exam does not exist.'), 404

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
        400 error if not all submissions from exam are validated
        (because we might send wrong emails this way).
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

        if not all(sub.validated for sub in exam.submissions):
            abort(
                409,
                message="All copies must be validated before sending emails."
            )

        if student_id is not None:
            return self._send_single(exam, student_id, template, attach, copy_to)
        else:
            return self._send_all(exam, template, attach)

    def _send_single(self, exam, student_id, template, attach, copy_to):
        if not (current_app.config.get('SMTP_SERVER') and current_app.config.get('FROM_ADDRESS')):
            abort(
                500,
                message='Sending email is not configured'
            )
        student = Student.query.get(student_id)
        sent, failed = emails.build_and_send(
            [student],
            from_address=current_app.config['FROM_ADDRESS'],
            exam=exam,
            template=template,
            attach=attach
        )
        if failed:
            abort(
                500,
                message=f'Failed to send email to student #{student_id}'
            )
        return dict(status=200)

    def _send_all(self, exam, template, attach):
        if not (current_app.config.get('SMTP_SERVER') and current_app.config.get('FROM_ADDRESS')):
            abort(
                500,
                message='Sending email is not configured'
            )

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
                    message='Failed to send some emails',
                    sent=sent,
                    failed=failed
                ), 206
            else:
                return dict(
                    status=500,
                    message='Failed to send emails',
                    failed=failed,
                ), 500

        return dict(status=200)
