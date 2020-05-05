import pytest

from flask import json

from zesje.database import db, Exam, Problem, FeedbackOption, Student, Submission


@pytest.fixture
def add_test_data(app):
    exam = Exam(name='exam 1', finalized=True)
    db.session.add(exam)

    problem1 = Problem(name='Problem 1', exam=exam)
    problem2 = Problem(name='Problem 2', exam=exam)
    db.session.add(problem1)
    db.session.add(problem2)

    feedback_option = FeedbackOption(problem=problem1, text='text', description='desc', score=5)
    db.session.add(feedback_option)

    student = Student(id=1000001, first_name='', last_name='')
    db.session.add(student)

    sub = Submission(exam=exam, student=student, copies=[], validated=True)
    db.session.add(sub)
    db.session.commit()

    yield app, exam


def test_get_statistics(test_client, add_test_data):
    app, exam = add_test_data

    response = test_client.get(f'/api/stats/{exam.id}')
    data = json.loads(response.data)

    assert len(data['problems']) == 1
