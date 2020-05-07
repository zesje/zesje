import os
from os.path import abspath, dirname

from flask import Flask, session, redirect, request, url_for, render_template
from flask_migrate import Migrate
from werkzeug.exceptions import NotFound
from flask_login import login_required, login_user, logout_user
from requests_oauthlib import OAuth2Session


from .database import db, login_manager, Grader
from .api import api_bp


STATIC_FOLDER_PATH = os.path.join(abspath(dirname(__file__)), 'static')


def create_app(celery=None, app_config=None):
    app = Flask(__name__, static_folder=STATIC_FOLDER_PATH)
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    login_manager.init_app(app)
    login_manager.login_view = "login"

    create_config(app.config, app_config)

    if celery is not None:
        attach_celery(app, celery)

    db.init_app(app)
    Migrate(app, db)

    app.register_blueprint(api_bp, url_prefix='/api')

    @app.before_first_request
    def setup():
        os.makedirs(app.config['DATA_DIRECTORY'], exist_ok=True)
        os.makedirs(app.config['SCAN_DIRECTORY'], exist_ok=True)

    @app.route('/')
    @app.route('/<path:path>')
    @login_required
    def index(path='index.html'):
        """Serve the static react content, otherwise fallback to the index.html
        React Router will decide what to do with the URL in that case.
        """

        try:
            return app.send_static_file(path)
        except NotFound:
            return render_template('index.html')

    @app.route("/login")
    def login():
        """Logs the user in by redirecting to the OAuth provider with the appropriate
        client ID as a request parameter"""
        github = OAuth2Session(app.config['OAUTH_CLIENT_ID'])
        authorization_url, state = github.authorization_url(app.config['OAUTH_AUTHORIZATION_BASE_URL'])

        session['oauth_state'] = state

        return redirect(authorization_url)

    @app.route("/callback")
    def callback():
        """OAuth provider redirects to this route after authorization.
        Fetches token and redirects to /profile"""
        gitlab = OAuth2Session(app.config['OAUTH_CLIENT_ID'], state=session['oauth_state'])
        token = gitlab.fetch_token(
            app.config['OAUTH_TOKEN_URL'],
            client_secret=app.config['OAUTH_CLIENT_SECRET'],
            authorization_response=request.url,
        )

        session['oauth_token'] = token  # token can used to make requests with OAuth provider later if needed

        github = OAuth2Session(app.config['OAUTH_CLIENT_ID'], token=session['oauth_token'])
        current_grader = github.get(app.config['OAUTH_USERINFO_URL']).json()
        session['grader_name'] = current_grader['name']

        grader = Grader.query.filter(Grader.name == current_grader['name']).one_or_none()

        if grader is None:
            grader = Grader(name=current_grader['name'])
            db.session.add(grader)
            db.session.commit()

        login_user(grader)

        return redirect(url_for('index'))

    @app.route("/logout", methods=["GET"])
    def logout():
        """Logs the user out and redirects to /login
        """
        logout_user()
        return redirect(url_for('.login'))

    return app


def attach_celery(app, celery):
    celery.conf.update(
        result_backend=app.config['CELERY_RESULT_BACKEND'],
        broker_url=app.config['CELERY_RESULT_BACKEND'],
    )
    TaskBase = celery.Task

    # Custom task class to ensure Celery tasks are run in the Flask app context
    class ContextTask(TaskBase):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    celery.Task = ContextTask


def create_config(config_instance, extra_config):
    # use default config as base
    config_instance.from_object('zesje_default_cfg')

    # apply user config
    if 'ZESJE_SETTINGS' in os.environ:
        config_instance.from_envvar('ZESJE_SETTINGS')

    # extra config?
    if extra_config is not None:
        config_instance.update(extra_config)

    # overwrite user config with constants
    config_instance.from_object('zesje.constants')

    # Make DATA_DIRECTORY absolute
    config_instance.update(
        DATA_DIRECTORY=abspath(config_instance['DATA_DIRECTORY']),
    )

    # These reference DATA_DIRECTORY, so they need to be in a separate update
    config_instance.update(
        SCAN_DIRECTORY=os.path.join(config_instance['DATA_DIRECTORY'], 'scans'),
        DB_PATH=os.path.join(config_instance['DATA_DIRECTORY'], 'course.sqlite'),
    )

    user = config_instance['MYSQL_USER']
    password = config_instance['MYSQL_PASSWORD']
    host = config_instance['MYSQL_HOST']
    database = config_instance['MYSQL_DATABASE']
    connector = config_instance['MYSQL_CONNECTOR']

    # Force MySQL to use a TCP connection
    host = host.replace('localhost', '127.0.0.1')
    # Interpret None as no password
    password = password if password is not None else ''

    config_instance.update(
        MYSQL_HOST=host,
        MYSQL_DIRECTORY=os.path.join(config_instance['DATA_DIRECTORY'], 'mysql'),
        SQLALCHEMY_DATABASE_URI=f'{connector}://{user}:{password}@{host}/{database}',
        SQLALCHEMY_PASSWORD=password,
        SQLALCHEMY_TRACK_MODIFICATIONS=False  # Suppress future deprecation warning
    )

    config_instance.update(
        CELERY_BROKER_URL='redis://localhost:6479',
        CELERY_RESULT_BACKEND='redis://localhost:6479'
    )
