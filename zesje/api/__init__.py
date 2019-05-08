from flask import Blueprint
from flask_restful import Api

from .graders import Graders
from .exams import Exams, ExamSource, ExamGeneratedPdfs, ExamPreview
from .scans import Scans
from .students import Students
from .submissions import Submissions
from .problems import Problems
from .feedback import Feedback
from .solutions import Solutions
from .widgets import Widgets
from .emails import EmailTemplate, RenderedEmailTemplate, Email
from .mult_choice import MultipleChoice
from . import signature
from . import images
from . import summary_plot
from . import export

api_bp = Blueprint(__name__, __name__)

api = Api(api_bp)

api.add_resource(Graders, '/graders')
api.add_resource(Exams, '/exams', '/exams/<int:exam_id>', '/exams/<int:exam_id>/<string:attr>')
api.add_resource(ExamSource, '/exams/<int:exam_id>/source_pdf')
api.add_resource(ExamGeneratedPdfs, '/exams/<int:exam_id>/generated_pdfs')
api.add_resource(ExamPreview, '/exams/<int:exam_id>/preview')
api.add_resource(Scans, '/scans/<int:exam_id>')
api.add_resource(Students, '/students', '/students/<int:student_id>')
api.add_resource(Submissions,
                 '/submissions/<int:exam_id>',
                 '/submissions/<int:exam_id>/<int:submission_id>')
api.add_resource(Problems,
                 '/problems',
                 '/problems/<int:problem_id>',
                 '/problems/<int:problem_id>/<string:attr>')
api.add_resource(Feedback,
                 '/feedback/<int:problem_id>',
                 '/feedback/<int:problem_id>/<int:feedback_id>')
api.add_resource(Solutions, '/solution/<int:exam_id>/<int:submission_id>/<int:problem_id>')
api.add_resource(Widgets,
                 '/widgets',
                 '/widgets/<int:widget_id>')
api.add_resource(EmailTemplate,
                 '/templates/<int:exam_id>')
api.add_resource(RenderedEmailTemplate,
                 '/templates/rendered/<int:exam_id>/<int:student_id>')
api.add_resource(Email,
                 '/email/<int:exam_id>',
                 '/email/<int:exam_id>/<int:student_id>')
api.add_resource(MultipleChoice, '/mult-choice/<int:id>')


# Other resources that don't return JSON
# It is possible to get flask_restful to work with these, but not
# very idiomatic.

# Images
api_bp.add_url_rule(
    '/images/signature/<int:exam_id>/<int:submission_id>',
    'signature',
    signature.get,
)
api_bp.add_url_rule(
    '/images/solutions/<int:exam_id>/<int:problem_id>/<int:submission_id>/<int:full_page>',
    'solution_image',
    images.get,
)
api_bp.add_url_rule(
    '/images/summary/<int:exam_id>',
    'exam_summary',
    summary_plot.get,
)

# Exports
api_bp.add_url_rule(
    '/export/full',
    'full_export',
    export.full,
)
api_bp.add_url_rule(
    '/export/<string:file_format>/<int:exam_id>',
    'dataframe_export',
    export.exam,
)
