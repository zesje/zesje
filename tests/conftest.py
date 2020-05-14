import os
import sys

import pytest
from _pytest.monkeypatch import MonkeyPatch
from flask import Flask
from pathlib import Path
from tempfile import TemporaryDirectory
from sqlalchemy.orm.session import close_all_sessions
from sqlalchemy import event, create_engine

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
        db.create_all()

    close_all_sessions()

    engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
    connection = engine.connect()
    app.config['TESTING_CONNECTION'] = connection

    app.register_blueprint(api_bp, url_prefix='/api')
    return app


def app_fixture(base_app, monkeypatch):
    app = base_app

    with TemporaryDirectory() as temp_dir:
        app.config.update(
            DATA_DIRECTORY=str(temp_dir),
            SCAN_DIRECTORY=str(temp_dir)
        )

        with app.app_context():
            connection = app.config['TESTING_CONNECTION']
            transaction = connection.begin()

            options = dict(bind=connection, binds={})
            session = db.create_scoped_session(options=options)
            session.begin_nested()

            @event.listens_for(session, 'after_transaction_end')
            def restart_savepoint(session2, transaction):
                # Detecting whether this is indeed the nested transaction of the test
                if transaction.nested and not transaction._parent.nested:
                    # The test should have normally called session.commit(),
                    # but to be safe we explicitly expire the session
                    session2.expire_all()
                    session.begin_nested()

            monkeypatch.setattr(db, 'session', session)

            yield app

            session.remove()
            transaction.rollback()


@pytest.fixture
def app(base_app, monkeypatch):
    yield from app_fixture(base_app, monkeypatch)


@pytest.fixture(scope='module')
def module_app(base_app, module_monkeypatch):
    yield from app_fixture(base_app, module_monkeypatch)


@pytest.fixture
def test_client(app):
    with app.test_client() as client:
        yield client


@pytest.fixture(scope='module')
def module_monkeypatch():
    monkeypatch = MonkeyPatch()
    yield monkeypatch
    monkeypatch.undo()
