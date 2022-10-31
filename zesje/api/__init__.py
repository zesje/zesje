from traceback import format_exc

from flask import current_app, request, Blueprint, jsonify
from flask_login import current_user
from werkzeug.exceptions import HTTPException

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
from .oauth import OAuthStart, OAuthCallback, OAuthStatus, OAuthLogout

from . import signature
from . import images
from . import export

from ..constants import EXEMPT_ROUTES, EXEMPT_METHODS


def check_user_login():
    """Checks if the user is logged in before proceding with the request.

    A 401 UNAUTHORIZED response is returned when all the following conditions are true:
    - The endpoint does not belong to the exempt routes
    - The method does not belong to the exempt methods
    - Login is not disabled (only during testing)
    - There is no logged in user.

    Note: returning `None` makes flask continue with the request.

    See Also
    --------
    `flask_login.login_required
    https://flask-login.readthedocs.io/en/latest/_modules/flask_login/utils.html#login_required`_
    """
    if current_app.config.get('LOGIN_DISABLED'):
        return None
    elif request.endpoint in EXEMPT_ROUTES or request.method in EXEMPT_METHODS:
        return None
    elif not current_user.is_authenticated:
        return current_app.login_manager.unauthorized()


def add_url_rules(bp, view_class, *rules, name=None):
    view_func = view_class.as_view(name or view_class.__name__.lower())
    for rule in rules:
        bp.add_url_rule(rule, view_func=view_func)


def handle_exception(e):
    # pass through HTTP errors
    if isinstance(e, HTTPException):
        return jsonify({
            'status': e.code,
            'name': e.name,
            'message': e.description,
            'description': None
        }), e.code

    # now you're handling non-HTTP exceptions only
    return jsonify({
        'status': 500,
        'name': 'Internal Python Exception',
        'message': str(e),
        'description': format_exc()
    }), 500


api_bp = Blueprint('zesje', __name__)
api_bp.before_request(check_user_login)
api_bp.register_error_handler(Exception, handle_exception)

add_url_rules(api_bp, Graders, '/graders')
add_url_rules(api_bp, Exams, '/exams', '/exams/<int:exam>', '/exams/<int:exam>/<string:attr>')
add_url_rules(api_bp, ExamSource, '/exams/<int:exam>/source_pdf', name='exam_source')
add_url_rules(api_bp, ExamGeneratedPdfs, '/exams/<int:exam>/generated_pdfs', name='exam_generated_pdfs')
add_url_rules(api_bp, ExamPreview, '/exams/<int:exam>/preview', 'exam_preview')
add_url_rules(api_bp, Scans, '/scans/<int:exam>')
add_url_rules(api_bp, Students, '/students', '/students/<int:student>')
add_url_rules(api_bp, Copies, '/copies/<int:exam>', '/copies/<int:exam>/<int:copy_number>')
add_url_rules(api_bp, MissingPages, '/copies/missing_pages/<int:exam>', name='missing_pages')
add_url_rules(api_bp, Submissions, '/submissions/<int:exam>', '/submissions/<int:exam>/<int:submission>')
add_url_rules(api_bp, Problems, '/problems', '/problems/<int:problem>')
add_url_rules(api_bp, Feedback, '/feedback/<int:problem>', '/feedback/<int:problem>/<int:feedback>')
add_url_rules(api_bp, Solutions, '/solution/<int:exam>/<int:submission>/<int:problem>')
add_url_rules(api_bp, Widgets, '/widgets', '/widgets/<int:widget>')
add_url_rules(api_bp, EmailTemplate, '/templates/<int:exam>', name='exam_template')
add_url_rules(api_bp, RenderedEmailTemplate, '/templates/rendered/<int:exam_id>/<int:student_id>',
              name='rendered_exam_template')
add_url_rules(api_bp, Email, '/email/<int:exam>', '/email/<int:exam>/<int:student>')
add_url_rules(api_bp, Approve, '/solution/approve/<int:exam>/<int:submission>/<int:problem>')
add_url_rules(api_bp, MultipleChoice, '/mult-choice/<int:mc_option>', '/mult-choice/', name='multiple_choice')
add_url_rules(api_bp, Statistics, '/stats/<int:exam>')
add_url_rules(api_bp, OAuthStatus, '/oauth/status', name='oauth_status')
add_url_rules(api_bp, OAuthStart, '/oauth/start', name='oauth_start')
add_url_rules(api_bp, OAuthCallback, '/oauth/callback', name='oauth_callback')
add_url_rules(api_bp, OAuthLogout, '/oauth/logout', name='oauth_logout')

# Images
api_bp.add_url_rule(
    '/images/signature/<int:exam>/<int:copy_number>',
    'signature',
    signature.get,
)
api_bp.add_url_rule(
    '/images/solutions/<int:exam>/<int:problem>/<int:submission>/<int:full_page>',
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
