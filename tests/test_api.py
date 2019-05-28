import pytest

from flask import Flask, json
from zesje.api import api_bp
from zesje.database import db, Exam, Problem, ProblemWidget


def add_test_data():
    exam1 = Exam(id=1, name='exam 1', finalized=False)
    exam2 = Exam(id=2, name='exam 2', finalized=True)
    exam3 = Exam(id=3, name='exam 3', finalized=False)

    db.session.add(exam1)
    db.session.add(exam2)
    db.session.add(exam3)
    db.session.commit()

    problem1 = Problem(id=1, name='Problem 1', exam_id=1)
    problem2 = Problem(id=2, name='Problem 2', exam_id=2)
    problem3 = Problem(id=3, name='Problem 3', exam_id=3)

    db.session.add(problem1)
    db.session.add(problem2)
    db.session.add(problem3)
    db.session.commit()

    problem_widget_1 = ProblemWidget(id=3, name='problem widget', problem_id=3, page=2,
                                     width=100, height=150, x=40, y=200, type='problem_widget')
    db.session.add(problem_widget_1)
    db.session.commit()


def delete_test_data():
    db.session.query(Exam).delete()
    db.session.commit()

    db.session.query(Problem).delete()
    db.session.commit()

    db.session.query(ProblemWidget).delete()
    db.session.commit()


@pytest.fixture()
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


'''
MULTIPLE CHOICE OPTION TESTS
'''


def not_present(test_client):
    result = test_client.get('/api/mult-choice/1')
    data = json.loads(result.data)

    assert data['message'] == "Multiple choice question with id 1 does not exist."


def test_add(test_client):
    req = mco_json()
    response = test_client.put('/api/mult-choice/', data=req)

    data = json.loads(response.data)

    assert data['message'] == 'New multiple choice question with id 4 inserted. ' \
        + 'New feedback option with id 1 inserted.'

    assert data['mult_choice_id'] == 4
    assert data['status'] == 200


def test_add_get(test_client):
    req = mco_json()

    response = test_client.put('/api/mult-choice/', data=req)
    data = json.loads(response.data)

    id = data['mult_choice_id']

    result = test_client.get(f'/api/mult-choice/{id}')
    data = json.loads(result.data)

    exp_resp = {
        'id': 4,
        'name': 'test',
        'x': 100,
        'y': 40,
        'type': 'mcq_widget',
        'feedback_id': 1,
        'label': 'a',
    }

    assert exp_resp == data


def test_update_put(test_client):
    req = mco_json()

    response = test_client.put('/api/mult-choice/', data=req)
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

    result = test_client.put(f'/api/mult-choice/{id}', data=req2)
    data = json.loads(result.data)

    assert data['message'] == f'Multiple choice question with id {id} updated'


def test_delete(test_client):
    req = mco_json()

    response = test_client.put('/api/mult-choice/', data=req)
    data = json.loads(response.data)
    id = data['mult_choice_id']

    response = test_client.delete(f'/api/mult-choice/{id}')
    data = json.loads(response.data)

    assert data['status'] == 200


def test_delete_not_present(test_client):
    id = 100

    response = test_client.delete(f'/api/mult-choice/{id}')
    data = json.loads(response.data)

    assert data['message'] == f'Multiple choice question with id {id} does not exist.'


def test_delete_finalized_exam(test_client):
    mc_option_json = {
        'x': 100,
        'y': 40,
        'problem_id': 2,
        'page': 1,
        'label': 'a',
        'name': 'test'
    }

    response = test_client.put('/api/mult-choice/', data=mc_option_json)
    data = json.loads(response.data)
    mc_id = data['mult_choice_id']

    response = test_client.delete(f'/api/mult-choice/{mc_id}')
    data = json.loads(response.data)

    assert data['status'] == 401


'''
EXAM API TESTS
'''


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

    assert len(data['problems'][0]['mc_options']) == 2
