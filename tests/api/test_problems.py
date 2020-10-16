import pytest
from datetime import datetime

from zesje.database import db, Exam, ExamLayout, Problem, FeedbackOption,\
                           ProblemWidget, Student, Submission, Solution, Grader


@pytest.fixture
def add_test_data(app):
    for layout in ExamLayout:
        id = layout.value
        exam = Exam(id=id, name=f'exam {layout.name}', finalized=True, layout=layout)
        db.session.add(exam)

        problem = Problem(id=id, name=f'Problem {layout.name}', exam_id=id)
        db.session.add(problem)

        problem_widget = ProblemWidget(id=id, name=f'problem widget {layout.name}', problem_id=id, page=2,
                                       width=100, height=150, x=40, y=200, type='problem_widget')
        db.session.add(problem_widget)
        db.session.commit()

        feedback_option = FeedbackOption(id=id, problem_id=id, text='text', description='desc', score=1)
        db.session.add(feedback_option)
        db.session.commit()

    yield app


@pytest.mark.parametrize('id, status', [
    (1, 200),
    (2, 200),
    (42, 404)
], ids=['Exists Templated', 'Exists unstructured', 'Not exists'])
def test_get_problem(test_client, add_test_data, id, status):
    result = test_client.get(f'/api/problems/{id}')

    assert result.status_code == status


@pytest.mark.parametrize('exam_id, position, status', [
    (1, (-1, 4, 400, 200), 409),
    (1, (10, -5, 400, 200), 409),
    (1, (10, 10, 800, 200), 409),
    (1, (10, 700, 400, 500), 409),
    (2, (-24, 5, 10000, 200), 200)
], ids=['Exceeds left', 'Exceeds top', 'Exceeds right', 'Exceeds bottom', 'Allowed unstructured'])
def test_add_problem(test_client, add_test_data, exam_id, position, status):
    req_body = {
        'exam_id': exam_id,
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
    (2, 200),
    (42, 404),
], ids=['Allowed templated', 'Allowed unstructured', 'Not exists'])
def test_rename_problem(test_client, add_test_data, id, status):
    new_name = 'New'
    result = test_client.put(f'/api/problems/{id}', data={'name': new_name})

    assert result.status_code == status
    if status == 200:
        assert Problem.query.get(id).name == new_name


@pytest.mark.parametrize('id, status', [
    (1, 200),
    (2, 200),
    (42, 404),
], ids=['Allowed templated', 'Allowed unstructured', 'Not exists'])
def test_delete_problem(test_client, add_test_data, id, status):
    result = test_client.delete(f'/api/problems/{id}')

    assert result.status_code == status
    assert Problem.query.get(id) is None


@pytest.mark.parametrize('exam_id, problem_id', [
    (1, 1),
    (2, 2),
], ids=['Templated', 'Unstructured'])
def test_delete_problem_graded(test_client, add_test_data, exam_id, problem_id):
    student = Student(first_name='', last_name='')
    db.session.add(student)
    grader = Grader(name='Zesje', oauth_id='zesje')
    db.session.add(grader)
    db.session.commit()
    sub = Submission(student=student, exam_id=exam_id)
    db.session.add(sub)
    db.session.commit()
    sol = Solution(problem_id=problem_id, submission=sub, graded_by=grader, graded_at=datetime.now())
    db.session.add(sol)
    db.session.commit()

    result = test_client.delete(f'/api/problems/{problem_id}')

    assert result.status_code == 403
    assert Problem.query.get(problem_id) is not None
