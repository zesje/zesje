import os
from tempfile import TemporaryDirectory

import pytest
import MySQLdb
from flask import Flask
from pathlib import Path
import sys

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
def db_app(config_app, mysql_proc):
    app = config_app

    # before actually creating the Flask connection we need to create the database
    mysqlconn = MySQLdb.connect(
        host='localhost',
        unix_socket=mysql_proc.unixsocket.strpath,
        user='root',
        passwd=''
    )

    mysqlconn.query('CREATE DATABASE IF NOT EXISTS course;')
    mysqlconn.query('USE course;')
    mysqlconn.close()

    app.config.update(
        SQLALCHEMY_DATABASE_URI=f'mysql://root:@localhost/course?unix_socket={mysql_proc.unixsocket.strpath}',
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
