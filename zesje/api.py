from flask import Blueprint
from flask_restful import Api

from .resources.graders import Graders
from .resources.exams import Exams, ExamSource, ExamGenerateds
from .resources.pdfs import Pdfs
from .resources.students import Students
from .resources.submissions import Submissions
from .resources import signature
from .resources import images
from .resources import summary_plot
from .resources import export
from .resources.problems import Problems
from .resources.feedback import Feedback
from .resources.solutions import Solutions
from .resources.widgets import Widgets

api_bp = Blueprint(__name__, __name__)

errors = {
    'ObjectNotFound': {
        'status': 404,
        'message': 'Resource with that ID does not exist',
     },
}

api = Api(api_bp, errors=errors)

api.add_resource(Graders, '/graders')
api.add_resource(Exams, '/exams', '/exams/<int:exam_id>')
api.add_resource(ExamSource, '/exams/<int:exam_id>/source_pdf')
api.add_resource(ExamGenerateds,
                 '/exams/<int:exam_id>/generateds',
                 '/exams/<int:exam_id>/generateds/<int:copy_num>')
api.add_resource(Pdfs, '/pdfs/<int:exam_id>')
api.add_resource(Students, '/students', '/students/<int:student_id>')
api.add_resource(Submissions,
                 '/submissions/<int:exam_id>',
                 '/submissions/<int:exam_id>/<int:submission_id>')
api.add_resource(Problems,
                 '/problems',
                 '/problems/<int:problem_id>/<string:attr>')
api.add_resource(Feedback, '/feedback/<int:problem_id>')
api.add_resource(Solutions, '/solution/<int:exam_id>/<int:submission_id>/<int:problem_id>')
api.add_resource(Widgets,
                 '/widgets',
                 '/widgets/<int:widget_id>')


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
    '/images/solutions/<int:exam_id>/<int:problem_id>/<int:submission_id>',
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
