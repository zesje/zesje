import os
from os.path import abspath, dirname

from flask import Flask
from flask_migrate import Migrate
from flask_session import Session
from werkzeug.exceptions import NotFound

from .database import db, login_manager, Grader
from .api import api_bp

STATIC_FOLDER_PATH = os.path.join(abspath(dirname(__file__)), "static")


def create_base_app(celery=None, app_config=None):
    """ Creates an app instance with only the config initialized """
    app = Flask(__name__, static_folder=STATIC_FOLDER_PATH)
    create_config(app.config, app_config)
    return app


def create_migrations_app():
    """ App instance only used to run migrations

    It is not possible to use the main app instance as it executes database queries during initialization.
    """
    app = create_base_app()

    db.init_app(app)
    Migrate(app, db)

    return app


def create_app(celery=None, app_config=None):
    """ App instance used to run the api using wsgi """
    app = create_base_app(celery, app_config)

    if app.config["OAUTH_INSECURE_TRANSPORT"]:
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    if app.config["SECRET_KEY"] is None:
        raise KeyError

    Session(app)

    login_manager.init_app(app)

    if celery is not None:
        attach_celery(app, celery)

    db.init_app(app)

    app.register_blueprint(api_bp, url_prefix="/api")

    with app.app_context():
        os.makedirs(app.config["DATA_DIRECTORY"], exist_ok=True)
        os.makedirs(app.config["SCAN_DIRECTORY"], exist_ok=True)

        # Add instance owner and autograder to db if they don't already exist
        if Grader.query.filter(Grader.oauth_id == app.config["OWNER_OAUTH_ID"]).one_or_none() is None:
            db.session.add(Grader(oauth_id=app.config["OWNER_OAUTH_ID"], name=app.config["OWNER_NAME"]))
            db.session.commit()

    @app.route("/")
    @app.route("/<path:path>")
    def index(path="index.html"):
        """Serve the static react content, otherwise fallback to the index.html

        React Router will decide what to do with the URL in that case.
        """
        try:
            return app.send_static_file(path)
        except NotFound:
            return app.send_static_file("index.html")

    return app


def attach_celery(app, celery):
    celery.conf.update(
        result_backend=app.config["CELERY_RESULT_BACKEND"],
        broker_url=app.config["CELERY_RESULT_BACKEND"],
    )
    TaskBase = celery.Task

    # Custom task class to ensure Celery tasks are run in the Flask app context
    class ContextTask(TaskBase):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                # Force the task to use a new connection.
                # See: https://docs.sqlalchemy.org/en/14/core/pooling.html#pooling-multiprocessing
                db.engine.dispose(close=False)

                return TaskBase.__call__(self, *args, **kwargs)

    celery.Task = ContextTask


def create_config(config_instance, extra_config):
    # use default config as base
    config_instance.from_object("zesje_default_cfg")

    # apply user config
    if "ZESJE_SETTINGS" in os.environ:
        config_instance.from_envvar("ZESJE_SETTINGS")

    # extra config?
    if extra_config is not None:
        config_instance.update(extra_config)

    # overwrite user config with constants
    config_instance.from_object("zesje.constants")

    # Make DATA_DIRECTORY absolute
    config_instance.update(
        DATA_DIRECTORY=abspath(config_instance["DATA_DIRECTORY"]),
    )

    # These reference DATA_DIRECTORY, so they need to be in a separate update
    config_instance.update(
        SCAN_DIRECTORY=os.path.join(config_instance["DATA_DIRECTORY"], "scans"),
        DB_PATH=os.path.join(config_instance["DATA_DIRECTORY"], "course.sqlite"),
    )

    user = config_instance["MYSQL_USER"]
    password = config_instance["MYSQL_PASSWORD"]
    host = config_instance["MYSQL_HOST"]
    database = config_instance["MYSQL_DATABASE"]
    connector = config_instance["MYSQL_CONNECTOR"]

    # Force MySQL to use a TCP connection
    host = host.replace("localhost", "127.0.0.1")
    # Interpret None as no password
    password = password if password is not None else ""

    config_instance.update(
        MYSQL_HOST=host,
        MYSQL_DIRECTORY=os.path.join(config_instance["DATA_DIRECTORY"], "mysql"),
        SQLALCHEMY_DATABASE_URI=f"{connector}://{user}:{password}@{host}/{database}",
        SQLALCHEMY_PASSWORD=password,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,  # Suppress future deprecation warning
    )

    config_instance.update(CELERY_BROKER_URL="redis://localhost:6479", CELERY_RESULT_BACKEND="redis://localhost:6479")
