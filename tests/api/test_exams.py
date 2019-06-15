import pytest

from flask import json
from zesje.database import db, Exam, Problem, ProblemWidget


@pytest.fixture
def add_test_data(app):
    with app.app_context():
        exam1 = Exam(id=1, name='exam 1', finalized=False)
        db.session.add(exam1)
        db.session.commit()

        problem1 = Problem(id=1, name='Problem 1', exam_id=1)
        db.session.add(problem1)
        db.session.commit()

        problem_widget_1 = ProblemWidget(id=1, name='problem widget', problem_id=1, page=2,
                                         width=100, height=150, x=40, y=200, type='problem_widget')
        db.session.add(problem_widget_1)
        db.session.commit()


# Actual tests


def test_get_exams(test_client, add_test_data):
    mc_option_1 = {
        'x': 100,
        'y': 40,
        'problem_id': 1,
        'page': 1,
        'label': 'a',
        'name': 'test'
    }
    test_client.put('/api/mult-choice/', data=mc_option_1)

    mc_option_2 = {
        'x': 100,
        'y': 40,
        'problem_id': 1,
        'page': 1,
        'label': 'a',
        'name': 'test'
    }
    test_client.put('/api/mult-choice/', data=mc_option_2)

    response = test_client.get('/api/exams/1')
    data = json.loads(response.data)

    assert len(data['problems'][0]['mc_options']) == 2
