import os
from os.path import abspath, dirname

from flask import Flask
from flask_migrate import Migrate
from werkzeug.exceptions import NotFound

from .database import db
from .api import api_bp


STATIC_FOLDER_PATH = os.path.join(abspath(dirname(__file__)), 'static')


def create_app(celery=None, app_config=None):
    app = Flask(__name__, static_folder=STATIC_FOLDER_PATH)

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
    def index(path='index.html'):
        """Serve the static react content, otherwise fallback to the index.html

        React Router will decide what to do with the URL in that case.
        """
        try:
            return app.send_static_file(path)
        except NotFound:
            return app.send_static_file('index.html')

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
    psw = config_instance['MYSQL_PSW']
    host = config_instance['MYSQL_HOST']
    database = config_instance['MYSQL_DATABASE']

    # Force MySQL to use a TCP connection
    host = host.replace('localhost', '127.0.0.1')
    # Interpret None as no password
    psw = psw if psw is not None else ''

    config_instance.update(
        MYSQL_HOST=host,
        MYSQL_DIRECTORY=os.path.join(config_instance['DATA_DIRECTORY'], 'mysql'),
        SQLALCHEMY_DATABASE_URI=f'mysql://{user}:{psw}@{host}/{database}',
        SQLALCHEMY_PASSWORD=psw,
        SQLALCHEMY_TRACK_MODIFICATIONS=False  # Suppress future deprecation warning
    )

    config_instance.update(
        CELERY_BROKER_URL='redis://localhost:6479',
        CELERY_RESULT_BACKEND='redis://localhost:6479'
    )
