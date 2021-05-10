import pytest

from flask import json

from zesje.database import db, Exam, Problem, ProblemWidget


@pytest.fixture
def add_test_data(app):
    exam1 = Exam(id=1, name='exam 1', finalized=False)
    db.session.add(exam1)

    problem1 = Problem(id=1, name='Problem 1', exam_id=1)
    db.session.add(problem1)

    problem_widget_1 = ProblemWidget(id=1, name='problem widget', problem_id=1, page=2,
                                     width=100, height=150, x=40, y=200, type='problem_widget')
    db.session.add(problem_widget_1)

    db.session.commit()


def fo_json():
    return {
        'name': "fully correct",
        'description': "",
        'score': 4
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
    data_get = data_get[0]
    assert data_get['name'] == 'fully correct'
