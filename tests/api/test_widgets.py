import pytest

from flask import json

from zesje.database import db, Exam, Problem, FeedbackOption, MultipleChoiceOption, ProblemWidget


@pytest.fixture
def add_test_data(app):
    with app.app_context():
        exam1 = Exam(id=1, name='exam 1', finalized=True)
        db.session.add(exam1)

        problem1 = Problem(id=1, name='Problem 1', exam_id=1, grading_policy=1)
        db.session.add(problem1)

        problem_widget_1 = ProblemWidget(id=1, name='problem widget', problem_id=1, page=2,
                                         width=100, height=150, x=40, y=200, type='problem_widget')
        db.session.add(problem_widget_1)
        db.session.commit()

        feedback_option = FeedbackOption(id=1, problem_id=1, text='text', description='desc', score=1)
        db.session.add(feedback_option)
        db.session.commit()

        mc_option = MultipleChoiceOption(id=2, label='a', feedback_id=1, x=10, y=30, name='mco', type='mcq_widget')
        db.session.add(mc_option)
        db.session.commit()


# Actual tests


def test_update_mco_finalized_exam(test_client, add_test_data):
    """
    Attempt to update a ProblemWidget in a finalized exam
    """
    widget_id = 2

    req_body = {'x': 50}

    result = test_client.patch(f'/api/widgets/{widget_id}', data=req_body)
    data = json.loads(result.data)

    assert data['status'] == 405
