import os
from os.path import abspath, dirname, pardir

from flask import Flask
from celery import Celery

from .database import db
from flask_migrate import Migrate

STATIC_FOLDER_PATH = os.path.join(abspath(dirname(__file__)), 'static')


def create_app():
    app = Flask(__name__, static_folder=STATIC_FOLDER_PATH)

    app.config.from_object('zesje_default_cfg')

    if 'ZESJE_SETTINGS' in os.environ:
        app.config.from_envvar('ZESJE_SETTINGS')

    # Make absolute path
    app.config.update(
        DATA_DIRECTORY=abspath(app.config['DATA_DIRECTORY']),
    )

    # These reference DATA_DIRECTORY, so they need to be in a separate update
    app.config.update(
        SCAN_DIRECTORY=os.path.join(app.config['DATA_DIRECTORY'], 'scans'),
        DB_PATH=os.path.join(app.config['DATA_DIRECTORY'], 'course.sqlite'),
    )

    app.config.update(
        SQLALCHEMY_DATABASE_URI='sqlite:///' + app.config['DB_PATH'],
        SQLALCHEMY_TRACK_MODIFICATIONS=False  # Suppress future deprecation warning
    )

    app.config.update(
        CELERY_BROKER_URL='redis://localhost:6479',
        CELERY_RESULT_BACKEND='redis://localhost:6479'
    )

    print(app.config['SQLALCHEMY_DATABASE_URI'])

    db.init_app(app)
    Migrate(app, db)

    return app


def make_celery(app=None):
    if app is None:
        app = create_app()

    celery = Celery(app.import_name,
                    backend=app.config['CELERY_RESULT_BACKEND'],
                    broker=app.config['CELERY_BROKER_URL'])

    celery.conf.update(app.config)
    TaskBase = celery.Task

    # Custom task class to ensure Celery tasks are run in the Flask app context
    class ContextTask(TaskBase):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    celery.Task = ContextTask

    return celery
