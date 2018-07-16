""" REST api for email templates """
from pathlib import Path
import textwrap

from jinja2 import Template, TemplateSyntaxError, UndefinedError

from flask import current_app as app
from flask_restful import Resource, reqparse

from pony import orm

from .. import emails
from ..database import Exam
from ._helpers import abort

default_email_template = textwrap.dedent(str.strip("""
    Dear {{student.first_name.split(' ') | first }} {{student.last_name}},

    Below please find attached the scans of your exam and our feedback.
    If you have any questions, don't hesitate to contant us.

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
    data_dir = Path(app.config['DATA_DIRECTORY'])
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
    except RuntimeError as error:
        if 'did not make a submission' in error.message:
            abort(
                400,
                message=f"Student #{student_id} did not make a "
                        "submission for this exam"
            )
        else:
            raise


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

        with orm.db_session:
            if not all(Exam[exam_id].submissions.signature_validated):
                return dict(
                    status=400,
                    message="All submissions must be validated before sending emails."
                ), 400

        if student_id is not None:
            student_ids = [student_id]
        else:
            with orm.db_session:
                student_ids = set(Exam[exam_id].submissions.student.id)

        messages = [
            emails.build(exam_id, student_id, template, attach=attach)
            for student_id in student_ids
        ]

        emails.send(messages)
