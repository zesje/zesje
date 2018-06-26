

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
