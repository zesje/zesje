import pytest

from flask import json
from flask import Flask

from zesje.api import api_bp
from zesje.database import db, Exam, Problem, ProblemWidget


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


def mco_json():
    return {
        'x': 100,
        'y': 40,
        'problem_id': 1,
        'page': 1,
        'label': 'a',
        'name': 'test'
    }


def add_test_data():
    exam1 = Exam(id=3, name='exam 1', finalized=False)

    db.session.add(exam1)
    db.session.commit()

    problem1 = Problem(id=3, name='Problem 1', exam_id=3)
    db.session.add(problem1)
    db.session.commit()

    problem_widget_1 = ProblemWidget(id=3, name='problem widget', problem_id=3, page=2,
                                     width=100, height=150, x=40, y=200, type='problem_widget')
    db.session.add(problem_widget_1)
    db.session.commit()


#####################
#    Actual test    #
#####################

def test_get_exams(test_client):
    mc_option_1 = {
        'x': 100,
        'y': 40,
        'problem_id': 3,
        'page': 1,
        'label': 'a',
        'name': 'test'
    }
    test_client.put('/api/mult-choice/', data=mc_option_1)

    mc_option_2 = {
        'x': 100,
        'y': 40,
        'problem_id': 3,
        'page': 1,
        'label': 'a',
        'name': 'test'
    }
    test_client.put('/api/mult-choice/', data=mc_option_2)

    response = test_client.get('/api/exams/3')
    data = json.loads(response.data)

    print(data)

    assert len(data['problems'][0]['mc_options']) == 2
