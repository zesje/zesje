from functools import wraps

from flask import current_app, request, Blueprint
from flask_restful import Api
from flask_login import current_user

from .graders import Graders
from .exams import Exams, ExamSource, ExamGeneratedPdfs, ExamPreview
from .scans import Scans
from .students import Students
from .copies import Copies, MissingPages
from .submissions import Submissions
from .problems import Problems
from .feedback import Feedback
from .solutions import Solutions, Approve
from .widgets import Widgets
from .emails import EmailTemplate, RenderedEmailTemplate, Email
from .mult_choice import MultipleChoice
from .statistics import Statistics
from .oauth import OAuthStart, OAuthCallback, OAuthGrader, OAuthLogout

from . import signature
from . import images
from . import export


def authenticate(func):
    """
    Function decorator that checks if the user is logged in before executing the actual function.
    If the user is not logged in it returns a 401 UNAUTHORIZED response.
    If the endpoint belongs to the exempt routes, the method belongs to the exempt methods or
    login is disabled (useful during development) the function is executed without checking for authentication.

    See Also
    --------
    `flask_login.login_required
    https://flask-login.readthedocs.io/en/latest/_modules/flask_login/utils.html#login_required`_
    """
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if request.endpoint in current_app.config['EXEMPT_ROUTES'] \
                or request.method in current_app.config['EXEMPT_METHODS']:
            return func(*args, **kwargs)
        elif current_app.config.get('LOGIN_DISABLED'):
            return func(*args, **kwargs)
        elif not current_user.is_authenticated:
            return current_app.login_manager.unauthorized()
        return func(*args, **kwargs)
    return decorated_view


api_bp = Blueprint(__name__, __name__)

api = Api(api_bp, decorators=[authenticate])

api.add_resource(Graders, '/graders')
api.add_resource(Exams, '/exams', '/exams/<int:exam_id>', '/exams/<int:exam_id>/<string:attr>')
api.add_resource(ExamSource, '/exams/<int:exam_id>/source_pdf')
api.add_resource(ExamGeneratedPdfs, '/exams/<int:exam_id>/generated_pdfs')
api.add_resource(ExamPreview, '/exams/<int:exam_id>/preview')
api.add_resource(Scans, '/scans/<int:exam_id>')
api.add_resource(Students, '/students', '/students/<int:student_id>')
api.add_resource(Copies,
                 '/copies/<int:exam_id>',
                 '/copies/<int:exam_id>/<int:copy_number>')
api.add_resource(MissingPages,
                 '/copies/missing_pages/<int:exam_id>')
api.add_resource(Submissions,
                 '/submissions/<int:exam_id>',
                 '/submissions/<int:exam_id>/<int:submission_id>')
api.add_resource(Problems,
                 '/problems',
                 '/problems/<int:problem_id>')
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
api.add_resource(Approve,
                 '/solution/approve/<int:exam_id>/<int:submission_id>/<int:problem_id>')
api.add_resource(MultipleChoice,
                 '/mult-choice/<int:id>',
                 '/mult-choice/')
api.add_resource(Statistics,
                 '/stats/<int:exam_id>')
api.add_resource(OAuthGrader, '/oauth/grader')
api.add_resource(OAuthStart, '/oauth/start')
api.add_resource(OAuthCallback, '/oauth/callback')
api.add_resource(OAuthLogout, '/oauth/logout')
# Other resources that don't return JSON
# It is possible to get flask_restful to work with these, but not
# very idiomatic.

# Images
api_bp.add_url_rule(
    '/images/signature/<int:exam_id>/<int:copy_number>',
    'signature',
    signature.get,
)
api_bp.add_url_rule(
    '/images/solutions/<int:exam_id>/<int:problem_id>/<int:submission_id>/<int:full_page>',
    'solution_image',
    images.get,
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
api_bp.add_url_rule(
    '/export/graders/<int:exam_id>',
    'grader_statistics_export',
    export.grader_statistics,
)
