import os

import pytest

from zesje.api import api_bp
from zesje.database import db, Exam, Problem, ProblemWidget
from flask import Flask


# Adapted from https://stackoverflow.com/a/46062148/1062698
@pytest.fixture
def datadir():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')


def add_test_data():
    exam1 = Exam(id=1, name='exam 1', finalized=False)
    exam2 = Exam(id=2, name='exam 2', finalized=True)
    exam3 = Exam(id=3, name='exam 1', finalized=False)

    db.session.add(exam1)
    db.session.add(exam2)
    db.session.add(exam3)
    db.session.commit()

    problem1 = Problem(id=1, name='Problem 1', exam_id=1)
    problem2 = Problem(id=2, name='Problem 2', exam_id=2)
    problem3 = Problem(id=3, name='Problem 1', exam_id=3)

    db.session.add(problem1)
    db.session.add(problem2)
    db.session.add(problem3)
    db.session.commit()

    problem_widget_1 = ProblemWidget(id=3, name='problem widget', problem_id=3, page=2,
                                     width=100, height=150, x=40, y=200, type='problem_widget')
    db.session.add(problem_widget_1)
    db.session.commit()


@pytest.fixture(scope="module")
def app():
    app = Flask(__name__, static_folder=None)

    app.config.update(
        SQLALCHEMY_DATABASE_URI='sqlite:///:memory:',
        SQLALCHEMY_TRACK_MODIFICATIONS=False  # Suppress future deprecation warning
    )
    db.init_app(app)

    with app.app_context():
        db.create_all()
        add_test_data()

    app.register_blueprint(api_bp, url_prefix='/api')

    return app


@pytest.fixture()
def test_client(app):
    client = app.test_client()

    yield client
