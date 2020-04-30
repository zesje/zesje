import os
import sys

import pytest
from flask import Flask
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path.cwd()))

from zesje.api import api_bp  # noqa: E402
from zesje.database import db  # noqa: E402
from zesje.factory import create_config  # noqa: E402


# Adapted from https://stackoverflow.com/a/46062148/1062698
@pytest.fixture
def datadir():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')


# Returns a Flask app with only the config initialized
# Runs only once per session
@pytest.fixture(scope='session')
def base_config_app():
    app = Flask(__name__, static_folder=None)
    create_config(app.config, None)
    return app

# Provides an app context, this runs for every test
# to ensure the app context is popped after each test
@pytest.fixture
def config_app(base_config_app):
    app = base_config_app
    with app.app_context():
        yield app


# Return a mock DB which can be used in the testing enviroment
# Session scope ensures it is ran only once
@pytest.fixture(scope="session")
def base_app(base_config_app):
    app = base_config_app

    app.config.update(
        SQLALCHEMY_DATABASE_URI='sqlite:///:memory:',
        SQLALCHEMY_TRACK_MODIFICATIONS=False  # Suppress future deprecation warning
    )
    db.init_app(app)
    app.register_blueprint(api_bp, url_prefix='/api')
    return app


def app_fixture(base_app):
    app = base_app

    with TemporaryDirectory() as temp_dir:
        app.config.update(
            DATA_DIRECTORY=str(temp_dir),
            SCAN_DIRECTORY=str(temp_dir)
        )

        with app.app_context():
            db.create_all()
            yield app
            db.drop_all()


@pytest.fixture
def app(base_app):
    for app in app_fixture(base_app):
        yield app


@pytest.fixture(scope='module')
def module_app(base_app):
    for app in app_fixture(base_app):
        yield app


@pytest.fixture
def test_client(app):
    with app.test_client() as client:
        yield client
