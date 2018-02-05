from flask import Blueprint
from flask_restful import Api

from .resources.graders import Graders
from .resources.exams import Exams, ExamConfig
from .resources.pdfs import Pdfs

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
