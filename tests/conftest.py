import os

import pytest
import MySQLdb
from flask import Flask
from zesje.api import api_bp
from zesje.database import db

# Adapted from https://stackoverflow.com/a/46062148/1062698
@pytest.fixture
def datadir():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')


@pytest.fixture(scope="module")
def app(mysql_proc):
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

    app = Flask(__name__, static_folder=None)

    app.config.update(
        SQLALCHEMY_DATABASE_URI=f'mysql://root:@localhost/course?unix_socket={mysql_proc.unixsocket.strpath}',
        SQLALCHEMY_TRACK_MODIFICATIONS=False  # Suppress future deprecation warning
    )
    db.init_app(app)

    with app.app_context():
        db.create_all()

    app.register_blueprint(api_bp, url_prefix='/api')

    return app


@pytest.fixture
def test_client(app):
    client = app.test_client()

    yield client

    with app.app_context():
        db.drop_all()
        db.create_all()


@pytest.fixture
def empty_app(app):
    with app.app_context():
        db.drop_all()
        db.create_all()

    return app


@pytest.fixture
def client(app):
    client = app.test_client()

    yield client

    with app.app_context():
        db.drop_all()
        db.create_all()
