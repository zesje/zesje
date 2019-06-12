import pytest

from flask import json

from zesje.database import db, Exam, Problem, ProblemWidget


@pytest.fixture
def add_test_data(app):
    with app.app_context():
        exam1 = Exam(id=1, name='exam 1', finalized=False)
        db.session.add(exam1)

        problem1 = Problem(id=1, name='Problem 1', exam_id=1, grading_policy=1)
        db.session.add(problem1)

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


'''
ACTUAL TESTS
'''


def test_delete_with_mc_option(test_client, add_test_data):
    """
    Attempt to delete a FeedbackOption related to a MultipleChoiceOption
    """
    req = mco_json()

    result = test_client.put('/api/mult-choice/', data=req)
    data = json.loads(result.data)

    assert data['feedback_id']

    fb_id = data['feedback_id']
    problem_id = 1  # Was inserted in add_test_data()

    result = test_client.delete(f'/api/feedback/{problem_id}/{fb_id}')
    data = json.loads(result.data)

    assert data['status'] == 401
