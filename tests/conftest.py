import os
from tempfile import TemporaryDirectory

import pytest
from flask import Flask
from zesje.api import api_bp
from zesje.database import db
from zesje.factory import create_config


# Adapted from https://stackoverflow.com/a/46062148/1062698
@pytest.fixture
def datadir():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')


# Return a mock DB which can be used in the testing enviroment
# Module scope ensures it is ran only once
@pytest.fixture(scope="module")
def db_app():
    app = Flask(__name__, static_folder=None)

    create_config(app.config, None)
    app.config.update(
        SQLALCHEMY_DATABASE_URI='sqlite:///:memory:',
        SQLALCHEMY_TRACK_MODIFICATIONS=False  # Suppress future deprecation warning
    )
    db.init_app(app)

    with TemporaryDirectory() as temp_dir:
        app.config.update(DATA_DIRECTORY=str(temp_dir))
        yield app


@pytest.fixture(scope="module")
def app(db_app):
    with db_app.app_context():
        db.create_all()

    db_app.register_blueprint(api_bp, url_prefix='/api')

    return db_app


@pytest.fixture
def test_client(app):
    client = app.test_client()

    yield client

    with app.app_context():
        db.drop_all()
        db.create_all()


@pytest.fixture
def client(app):
    client = app.test_client()

    yield client

    with app.app_context():
        db.drop_all()
        db.create_all()
