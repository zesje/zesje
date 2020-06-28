import pytest
from datetime import datetime

from zesje.database import db, Exam, Problem, FeedbackOption, ProblemWidget, Student, Submission, Solution, Grader


@pytest.fixture
def add_test_data(app):
    exam = Exam(id=1, name='exam 1', finalized=True)
    db.session.add(exam)

    problem = Problem(id=1, name='Problem 1', exam_id=1)
    db.session.add(problem)

    problem_widget = ProblemWidget(id=1, name='problem widget', problem_id=1, page=2,
                                   width=100, height=150, x=40, y=200, type='problem_widget')
    db.session.add(problem_widget)
    db.session.commit()

    feedback_option = FeedbackOption(id=1, problem_id=1, text='text', description='desc', score=1)
    db.session.add(feedback_option)
    db.session.commit()

    yield app, exam, problem


@pytest.mark.parametrize('id, status', [
    (1, 200),
    (42, 404)
], ids=['Exists', 'Not exists'])
def test_get_problem(test_client, add_test_data, id, status):
    result = test_client.get(f'/api/problems/{id}')

    assert result.status_code == status


@pytest.mark.parametrize('position, status', [
    ((-1, 4, 400, 200), 409),
    ((10, -5, 400, 200), 409),
    ((10, 10, 800, 200), 409),
    ((10, 700, 400, 500), 409)
], ids=['Exceeds left', 'Exceeds top', 'Exceeds right', 'Exceeds bottom'])
def test_add_problem(test_client, add_test_data, position, status):
    req_body = {
        'exam_id': 1,
        'x': position[0],
        'y': position[1],
        'width': position[2],
        'height': position[3],
        'page': 1,
        'name': 'Problem'
    }

    result = test_client.post('/api/problems', data=req_body)
    assert result.status_code == status


@pytest.mark.parametrize('id, status', [
    (1, 200),
    (42, 404),
], ids=['Exists', 'Not exists'])
def test_rename_problem(test_client, add_test_data, id, status):
    new_name = 'New'
    result = test_client.put(f'/api/problems/{id}', data={'name': new_name})

    assert result.status_code == status
    if status == 200:
        assert Problem.query.get(id).name == new_name


@pytest.mark.parametrize('id, status', [
    (1, 200),
    (42, 404),
], ids=['Exists', 'Not exists'])
def test_delete_problem(test_client, add_test_data, id, status):
    result = test_client.delete(f'/api/problems/{id}')

    assert result.status_code == status
    assert Problem.query.get(id) is None


def test_delete_problem_graded(test_client, add_test_data):
    app, exam, problem = add_test_data

    student = Student(first_name='', last_name='')
    db.session.add(student)
    grader = Grader(name='Zesje')
    db.session.add(grader)
    db.session.commit()
    sub = Submission(student=student, exam=exam)
    db.session.add(sub)
    db.session.commit()
    sol = Solution(problem=problem, submission=sub, graded_by=grader, graded_at=datetime.now())
    db.session.add(sol)
    db.session.commit()

    result = test_client.delete(f'/api/problems/{problem.id}')

    assert result.status_code == 403
    assert Problem.query.get(problem.id) is not None
