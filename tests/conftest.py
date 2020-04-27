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
@pytest.fixture(scope="module")
def config_app():
    app = Flask(__name__, static_folder=None)
    create_config(app.config, None)
    with app.app_context():
        yield app


# Return a mock DB which can be used in the testing enviroment
# Module scope ensures it is ran only once
@pytest.fixture(scope="module")
def db_app(config_app):
    app = config_app

    db.init_app(app)

    if 'GITLAB_TEST' in os.environ:
        app.config.update(SQLALCHEMY_DATABASE_URI=f'mysql://root:@mysql/course_test')
    else:
        user = app.config['MYSQL_USER']
        psw = app.config['MYSQL_PSW']
        app.config.update(SQLALCHEMY_DATABASE_URI=f'mysql://{user}:{psw}@localhost/course_test')

    with TemporaryDirectory() as temp_dir:
        app.config.update(
            DATA_DIRECTORY=str(temp_dir),
            SCAN_DIRECTORY=str(temp_dir)
        )

        yield app


@pytest.fixture(scope="module")
def app(db_app):
    with db_app.app_context():
        db.create_all()

    db_app.register_blueprint(api_bp, url_prefix='/api')

    return db_app


@pytest.fixture
def empty_app(app):
    with app.app_context():
        db.drop_all()
        db.create_all()
        yield app


@pytest.fixture
def test_client(app):
    client = app.test_client()

    yield client

    with app.app_context():
        db.drop_all()
        db.create_all()


@pytest.fixture
def client(empty_app):
    client = empty_app.test_client()

    yield client
