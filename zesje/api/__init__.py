from flask import current_app, request, Blueprint
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


api_bp = Blueprint('zesje', __name__)
api_bp.before_request(check_user_login)

api_bp.add_url_rule('/graders',
                    view_func=Graders.as_view('graders'))
api_bp.add_url_rule('/exams', '/exams/<int:exam_id>', '/exams/<int:exam_id>/<string:attr>',
                    view_func=Exams.as_view('exams'))
api_bp.add_url_rule('/exams/<int:exam_id>/source_pdf',
                    view_func=ExamSource.as_view('exam_source'))
api_bp.add_url_rule('/exams/<int:exam_id>/generated_pdfs',
                    view_func=ExamGeneratedPdfs.as_view('exam_generated_pdfs'))
api_bp.add_url_rule('/exams/<int:exam_id>/preview',
                    view_func=ExamPreview.as_view('exam_preview'))
api_bp.add_url_rule('/scans/<int:exam_id>',
                    view_func=Scans.as_view('scans'))
api_bp.add_url_rule('/students', '/students/<int:student_id>',
                    view_func=Students.as_view('students'))
api_bp.add_url_rule('/copies/<int:exam_id>', '/copies/<int:exam_id>/<int:copy_number>',
                    view_func=Copies.as_view('copies'))
api_bp.add_url_rule('/copies/missing_pages/<int:exam_id>',
                    view_func=MissingPages.as_view('missing_pages'))
api_bp.add_url_rule('/submissions/<int:exam_id>', '/submissions/<int:exam_id>/<int:submission_id>',
                    view_func=Submissions.as_view('submissions'))
api_bp.add_url_rule('/problems', '/problems/<int:problem_id>',
                    view_func=Problems.as_view('problems'))
api_bp.add_url_rule('/feedback/<int:problem_id>', '/feedback/<int:problem_id>/<int:feedback_id>',
                    view_func=Feedback.as_view('feedback'))
api_bp.add_url_rule('/solution/<int:exam_id>/<int:submission_id>/<int:problem_id>',
                    view_func=Solutions.as_view('solutions'))
api_bp.add_url_rule('/widgets', '/widgets/<int:widget_id>',
                    view_func=Widgets.as_view('widgets'))
api_bp.add_url_rule('/templates/<int:exam_id>',
                    view_func=EmailTemplate.as_view('exam_template'))
api_bp.add_url_rule('/templates/rendered/<int:exam_id>/<int:student_id>',
                    view_func=RenderedEmailTemplate.as_view('rendered_exam_template'))
api_bp.add_url_rule('/email/<int:exam_id>', '/email/<int:exam_id>/<int:student_id>',
                    view_func=Email.as_view('email'))
api_bp.add_url_rule('/solution/approve/<int:exam_id>/<int:submission_id>/<int:problem_id>',
                    view_func=Approve.as_view('approve'))
api_bp.add_url_rule('/mult-choice/<int:id>', '/mult-choice/',
                    view_func=MultipleChoice.as_view('multiple_choice'))
api_bp.add_url_rule('/stats/<int:exam_id>', view_func=Statistics.as_view('statistics'))
api_bp.add_url_rule('/oauth/status', view_func=OAuthStatus.as_view('oauth_status'))
api_bp.add_url_rule('/oauth/start', view_func=OAuthStart.as_view('oauth_start'))
api_bp.add_url_rule('/oauth/callback', view_func=OAuthCallback.as_view('oauth_callback'))
api_bp.add_url_rule('/oauth/logout', view_func=OAuthLogout.as_view('oauth_logout'))
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
