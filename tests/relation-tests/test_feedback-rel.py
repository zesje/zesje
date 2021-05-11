import pytest

from flask import json

from zesje.database import db, Exam, Problem, ProblemWidget, FeedbackOption


@pytest.fixture
def add_test_data(app):
    exam1 = Exam(id=1, name='exam 1', finalized=False)
    db.session.add(exam1)

    problem1 = Problem(id=1, name='Problem 1', exam_id=1)
    db.session.add(problem1)

    problem_widget_1 = ProblemWidget(id=1, name='problem widget', problem_id=1, page=2,
                                     width=100, height=150, x=40, y=200, type='problem_widget')
    db.session.add(problem_widget_1)

    fo1 = FeedbackOption(id=5, problem_id=1, text='fully incorrect', score=2)
    db.session.add(fo1)

    db.session.commit()


def fo_json():
    return {
        'name': "fully correct",
        'description': "",
        'score': 4
    }


def fo_parent_json():
    return {
        'name': "fully correct",
        'description': "",
        'score': 4,
        'parent': 5
    }

# Actual tests


def test_create_and_get_fo(test_client, add_test_data):
    fo = fo_json()

    result = test_client.post('/api/feedback/1', data=fo)
    data = json.loads(result.data)

    assert data['name'] == fo['name']
    assert data['description'] == fo['description']
    assert data['score'] == fo['score']

    result_get = test_client.get('/api/feedback/1')
    data_get = json.loads(result_get.data)
    data_get = data_get[1]
    assert data_get['name'] == 'fully correct'


def test_create_and_get_fo_with_parent(test_client, add_test_data):
    fo_p = fo_parent_json()

    result = test_client.post('api/feedback/1', data=fo_p)
    data = json.loads(result.data)

    assert data['parent'] == fo_p['parent']

    result_get = test_client.get('/api/feedback/1')
    data_get = json.loads(result_get.data)

    data_get = data_get[1]
    assert data_get['parent'] == 5


def test_delete_fo(test_client, add_test_data):
    fo = fo_json()

    result = test_client.post('/api/feedback/1', data=fo)
    data = json.loads(result.data)

    assert data['id']

    fb_id = data['id']
    problem_id = 1  # Was inserted in add_test_data()

    result_get = test_client.get('/api/feedback/1')
    data_get = json.loads(result_get.data)

    assert len(data_get) == 2

    result = test_client.delete(f'/api/feedback/{problem_id}/{fb_id}')
    data = json.loads(result.data)

    assert data['status'] == 200

    result_get = test_client.get('/api/feedback/1')
    data_get = json.loads(result_get.data)

    assert len(data_get) == 1


def test_delete_fo_with_parent(test_client, add_test_data):
    fop = fo_parent_json()

    result = test_client.post('/api/feedback/1', data=fop)
    data = json.loads(result.data)

    assert data['id']

    fb_id = data['id']
    problem_id = 1  # Was inserted in add_test_data()

    result_get = test_client.get('/api/feedback/1')
    data_get = json.loads(result_get.data)

    assert len(data_get) == 2

    result = test_client.delete(f'/api/feedback/{problem_id}/{fb_id}')
    data = json.loads(result.data)

    assert data['status'] == 200

    result_get = test_client.get('/api/feedback/1')
    data_get = json.loads(result_get.data)

    assert len(data_get) == 1
