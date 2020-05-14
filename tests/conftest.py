import os
import sys

import pytest
from flask import Flask
from pathlib import Path
from tempfile import TemporaryDirectory
from sqlalchemy.orm.session import close_all_sessions

sys.path.insert(0, str(Path.cwd()))

from zesje.api import api_bp  # noqa: E402
from zesje.database import db, login_manager  # noqa: E402
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
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    login_manager.init_app(app)

    @app.route('/')
    def index():
        """OAuth callback redirects to index. Required to build url for endpoint index"""
        return 'success'
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

    db.init_app(app)
    with app.app_context():
        db.drop_all()

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

            close_all_sessions()
            db.drop_all()


@pytest.fixture
def app(base_app):
    yield from app_fixture(base_app)


@pytest.fixture(scope='module')
def module_app(base_app):
    yield from app_fixture(base_app)


@pytest.fixture
def test_client(app):
    with app.test_client() as client:
        yield client
