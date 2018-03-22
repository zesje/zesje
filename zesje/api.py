from flask import Blueprint
from flask_restful import Api

from .resources.graders import Graders
from .resources.exams import Exams, ExamConfig
from .resources.pdfs import Pdfs
from .resources.students import Students
from .resources.submissions import Submissions
from .resources import signature
from .resources.problems import Problems

api_bp = Blueprint(__name__, __name__)

errors = {
    'ObjectNotFound': {
        'status': 404,
        'message': 'Resource with that ID does not exist',
     },
}

api = Api(api_bp, errors=errors)

api.add_resource(Graders, '/graders')
api.add_resource(Exams, '/exams')
api.add_resource(ExamConfig, '/exams/<int:exam_id>')
api.add_resource(Pdfs, '/pdfs/<int:exam_id>')
api.add_resource(Students, '/students', '/students/<int:student_id>')
api.add_resource(Submissions,
                 '/submissions/<int:exam_id>',
                 '/submissions/<int:exam_id>/<int:submission_id>')
api.add_resource(Problems, '/problems/<int:exam_id>')

# Other resources that don't return JSON
# It is possible to get flask_restful to work with these, but not
# very idiomatic.
api_bp.add_url_rule(
    '/images/signature/<int:exam_id>/<int:submission_id>',
    'signature',
    signature.get,
)
