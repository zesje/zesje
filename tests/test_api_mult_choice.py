import pytest
from flask import Flask, json

from zesje.api import api_bp
from zesje.database import db, Exam, Problem


def mco_json():
    return {
        'x': 100,
        'y': 40,
        'problem_id': 1,
        'page': 1,
        'label': 'a',
        'name': 'test'
    }


def add_exam(db, finalized=False):
    # Exam with id 1
    exam = Exam(name='exam', finalized=finalized)
    db.session.add(exam)
    db.session.commit()

    return exam


def add_problem(db, exam_id=1):
    problem = Problem(name='problem', exam_id=exam_id)
    db.session.add(problem)
    db.session.commit()

    return problem


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
        add_problem(db)
        add_exam(db)

    app.register_blueprint(api_bp, url_prefix='/api')

    return app


@pytest.fixture
def client(app):
    client = app.test_client()

    yield client


def test_get_no_exam(client):
    result = client.get('/api/mult-choice/1')
    data = json.loads(result.data)

    assert data['message'] == "Multiple choice question with id 1 does not exist."


def test_add_exam(client):
    req = mco_json()
    response = client.put('/api/mult-choice/', data=req)

    data = json.loads(response.data)

    assert data['message'] == 'New multiple choice question with id 1 inserted. ' \
        + 'New feedback option with id 1 inserted.'

    assert data['mult_choice_id'] == 1
    assert data['status'] == 200


def test_add_get(client):
    req = mco_json()

    response = client.put('/api/mult-choice/', data=req)
    data = json.loads(response.data)

    id = data['mult_choice_id']

    result = client.get(f'/api/mult-choice/{id}')
    data = json.loads(result.data)

    exp_resp = {
        'id': 2,
        'name': 'test',
        'x': 100,
        'y': 40,
        'type': 'mcq_widget',
        'feedback_id': 2,
        'label': 'a',
    }

    assert exp_resp == data


def test_update_put(client):
    req = mco_json()

    response = client.put('/api/mult-choice/', data=req)
    data = json.loads(response.data)
    id = data['mult_choice_id']

    req2 = {
        'x': 120,
        'y': 50,
        'problem_id': 4,
        'page': 1,
        'label': 'b',
        'name': 'test'
    }

    result = client.put(f'/api/mult-choice/{id}', data=req2)
    data = json.loads(result.data)

    assert data['message'] == f'Multiple choice question with id {id} updated'


def test_delete(client):
    req = mco_json()

    response = client.put('/api/mult-choice/', data=req)
    data = json.loads(response.data)
    id = data['mult_choice_id']

    response = client.delete(f'/api/mult-choice/{id}')
    data = json.loads(response.data)

    assert data['status'] == 200


def test_delete_not_present(client):
    id = 5

    response = client.delete(f'/api/mult-choice/{id}')
    data = json.loads(response.data)

    assert data['message'] == f'Multiple choice question with id {id} does not exist.'
