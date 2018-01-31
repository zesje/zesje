from flask import Blueprint
from flask_restful import Api

from .resources.graders import Graders
from .resources.exams import Exams, ExamConfig

api_bp = Blueprint(__name__, __name__)
api = Api(api_bp)

api.add_resource(Graders, '/graders')
api.add_resource(Exams, '/exams')
api.add_resource(ExamConfig, '/exams/<int:id>')
