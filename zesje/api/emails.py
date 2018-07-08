""" REST api for email templates """
from pathlib import Path

from jinja2 import Template, TemplateSyntaxError

from flask import current_app as app
from flask_restful import Resource, reqparse

from .. import emails


default_email_template = """Dear {{student.first_name.split(' ') | first }} {{student.last_name}},

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
Course team."""


def template_path(exam_id):
    data_dir = Path(app.config['DATA_DIRECTORY'])
    template_file = data_dir / f'{exam_id}_data' / 'email_template.j2'
    return template_file


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
        except TemplateSyntaxError:
            return dict(status=400, message="Syntax error in the template"), 400

        with open(template_path(exam_id), 'w') as f:
            f.write(email_template)


class Email(Resource):

    def get(self, exam_id, student_id):
        """Get an email text."""
        with open(template_path(exam_id)) as f:
            template = f.read()

        try:
            return emails.form_email(exam_id, student_id, template, text_only=True)
        except Exception:
            return dict(400, "Failed to format email."), 400


    def post(self, exam_id, student_id=None):
        """Send an email."""
        raise NotImplementedError  # To be continued
        with open(template_path(exam_id)) as f:
            template = f.read()

        if student_id is not None:
            result = emails.form_email(exam_id, student_id, template)
