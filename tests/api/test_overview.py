import pytest
from datetime import datetime

from flask import json

from zesje.database import db, Exam, Problem, FeedbackOption, Student, Submission, Solution, Grader


@pytest.fixture
def add_test_data(app):
    exam = Exam(id=1, name='exam 1', finalized=True)
    db.session.add(exam)

    grader = Grader(name='Anton', oauth_id='anton')
    db.session.add(grader)

    problem1 = Problem(id=1, name='Problem', exam=exam)
    problem2 = Problem(id=2, name='Empty Problem', exam=exam)
    problem3 = Problem(id=3, name='Extra Space', exam=exam)
    db.session.add_all([problem1, problem2, problem3])

    fo1_p1 = FeedbackOption(id=1, problem=problem1, text='text', description='desc', score=5)
    fo1_p3 = FeedbackOption(id=3, problem=problem3, text='blank', description='desc', score=0)
    db.session.add_all([fo1_p1, fo1_p3])

    student1 = Student(id=1000001, first_name='', last_name='')
    student2 = Student(id=1000002, first_name='', last_name='')
    db.session.add_all([student1, student2])

    sub1 = Submission(id=1, exam=exam, student=student1, copies=[], validated=True)
    db.session.add(sub1)

    sol_graded = Solution(id=1, submission=sub1, problem=problem1, graded_by=grader, graded_at=datetime.now())
    sol_graded.feedback.append(fo1_p1)
    sol_blank = Solution(id=2, submission=sub1, problem=problem3, graded_by=grader)
    sol_blank.feedback.append(fo1_p3)
    db.session.add_all([sol_graded, sol_blank])

    sub2 = Submission(id=2, exam=exam, student=student2, copies=[], validated=True)
    db.session.add(sub2)

    sol_revision = Solution(id=3, submission=sub2, problem=problem1, graded_by=None)
    sol_revision.feedback.append(fo1_p1)
    db.session.add(sol_revision)

    sub3 = Submission(id=3, exam=exam, student=student2, copies=[], validated=False)
    db.session.add(sub2)

    sol_not_validated = Solution(id=4, submission=sub3, problem=problem1, graded_by=grader, graded_at=datetime.now())
    sol_not_validated.feedback.append(fo1_p1)
    db.session.add(sol_revision)

    db.session.commit()

    yield app, exam


@pytest.fixture
def add_empty_data(app):
    exam = Exam(id=1, name='exam 1', finalized=True)
    db.session.add(exam)

    problems = [Problem(id=j, name=f'Problem {j}', exam=exam) for j in range(1, 3)]
    db.session.add_all(problems)

    fo = FeedbackOption(id=1, text='Blank', score=0, problem=problems[1])
    db.session.add(fo)
    db.session.commit()

    yield app, exam


def test_exam_exist(test_client, add_test_data):
    response = test_client.get('/api/stats/1')
    assert response.status_code == 200

    response = test_client.get('/api/stats/2')
    assert response.status_code == 404


def test_statistics(test_client, add_test_data):
    response = test_client.get('/api/stats/1')
    assert response.status_code == 200

    data = json.loads(response.data)

    # Only problems with at least one feedback option and a maximum score > 0 should be returned
    assert len(data['problems']) == 1

    p1 = data['problems'][0]

    # two validated solution in this problem
    assert len(p1['results']) == 2

    # One solution has feedback assigned but no grader
    assert p1['inRevision'] == 1

    # count partially graded problems
    total = data['total']['results']
    assert total[0]['ungraded'] == 0
    assert total[1]['ungraded'] == 1


def test_no_validated_students(test_client, add_empty_data):
    response = test_client.get('/api/stats/1')
    assert response.status_code == 404


def test_no_problems(app, test_client):
    db.session.add(Exam(id=1, name='Empty', finalized=True))
    db.session.commit()

    response = test_client.get('/api/stats/1')
    assert response.status_code == 404


def test_no_gradable_problems(test_client, add_empty_data):
    app, exam = add_empty_data

    student1 = Student(id=1000001, first_name='', last_name='')
    db.session.add(student1)

    sub1 = Submission(id=1, exam=exam, student=student1, copies=[], validated=True)
    db.session.add(sub1)

    response = test_client.get('/api/stats/1')
    assert response.status_code == 404
