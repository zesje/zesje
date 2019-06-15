import pytest

from flask import json

from zesje.database import db, Exam, Problem, ProblemWidget


@pytest.fixture
def add_test_data(app):
    with app.app_context():
        exam1 = Exam(id=1, name='exam 1', finalized=False)
        exam2 = Exam(id=2, name='exam 2', finalized=True)
        exam3 = Exam(id=3, name='exam 3', finalized=False)

        db.session.add(exam1)
        db.session.add(exam2)
        db.session.add(exam3)

        problem1 = Problem(id=1, name='Problem 1', exam_id=1)
        problem2 = Problem(id=2, name='Problem 2', exam_id=2)
        problem3 = Problem(id=3, name='Problem 3', exam_id=3)

        db.session.add(problem1)
        db.session.add(problem2)
        db.session.add(problem3)

        problem_widget_1 = ProblemWidget(id=1, name='problem widget', problem_id=1, page=2,
                                         width=100, height=150, x=40, y=200, type='problem_widget')
        db.session.add(problem_widget_1)

        db.session.commit()


def mco_json():
    return {
        'x': 100,
        'y': 40,
        'problem_id': 1,
        'page': 1,
        'label': 'a',
        'name': 'test'
    }


# ACTUAL TESTS


def test_not_present(test_client, add_test_data):
    result = test_client.get('/api/mult-choice/1')
    data = json.loads(result.data)

    assert data['status'] == 404


def test_problem_not_present(test_client, add_test_data):
    req_json = {
        'x': 100,
        'y': 40,
        'problem_id': 99,
        'page': 1,
        'label': 'a',
        'name': 'test'
    }

    result = test_client.put('/api/mult-choice/', data=req_json)
    data = json.loads(result.data)

    assert data['status'] == 404


def test_add(test_client, add_test_data):
    req = mco_json()

    response = test_client.put('/api/mult-choice/', data=req)
    data = json.loads(response.data)

    assert data['status'] == 200


def test_add_get(test_client, add_test_data):
    req = mco_json()

    response = test_client.put('/api/mult-choice/', data=req)
    data = json.loads(response.data)

    assert data['mult_choice_id']

    id = data['mult_choice_id']

    result = test_client.get(f'/api/mult-choice/{id}')
    data = json.loads(result.data)

    exp_resp = {
        'id': 2,
        'name': 'test',
        'x': 100,
        'y': 40,
        'type': 'mcq_widget',
        'feedback_id': 1,
        'label': 'a',
    }

    assert exp_resp == data


def test_update_patch(test_client, add_test_data):
    req = mco_json()

    response = test_client.put('/api/mult-choice/', data=req)
    data = json.loads(response.data)

    assert data['mult_choice_id']

    id = data['mult_choice_id']

    req2 = {
        'x': 120,
        'y': 50,
        'problem_id': 4,
        'page': 1,
        'label': 'b',
        'name': 'test'
    }

    result = test_client.patch(f'/api/mult-choice/{id}', data=req2)
    data = json.loads(result.data)

    assert data['status'] == 200


def test_delete(test_client, add_test_data):
    req = mco_json()

    response = test_client.put('/api/mult-choice/', data=req)
    data = json.loads(response.data)
    id = data['mult_choice_id']

    response = test_client.delete(f'/api/mult-choice/{id}')
    data = json.loads(response.data)

    assert data['status'] == 200


def test_delete_problem_check_mco(test_client, add_test_data):
    req = mco_json()
    problem_id = req['problem_id']

    response = test_client.put('/api/mult-choice/', data=req)
    data = json.loads(response.data)
    mult_choice_id = data['mult_choice_id']

    # Delete problem
    test_client.delete(f'/api/problems/{problem_id}')

    # Get mult choice option
    response = test_client.get(f'/api/mult-choice/{mult_choice_id}')
    data = json.loads(response.data)

    assert data['status'] == 404


def test_delete_mco_check_feedback(test_client, add_test_data):
    req = mco_json()

    response = test_client.put('/api/mult-choice/', data=req)
    data = json.loads(response.data)
    mult_choice_id = data['mult_choice_id']
    feedback_id = data['feedback_id']

    test_client.delete(f'/api/mult-choice/{mult_choice_id}')

    # Get feedback
    response = test_client.get(f'/api/feedback/{feedback_id}')
    data = json.loads(response.data)

    ids = [fb['id'] for fb in data]

    assert feedback_id not in ids


def test_delete_not_present(test_client, add_test_data):
    id = 100

    response = test_client.delete(f'/api/mult-choice/{id}')
    data = json.loads(response.data)

    assert data['status'] == 404


def test_delete_finalized_exam(test_client, add_test_data):
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
