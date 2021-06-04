import pytest

from flask import json

from zesje.database import db, Exam, Problem, ProblemWidget, ExamWidget
import zesje


@pytest.fixture
def add_test_data(app):
    exam1 = Exam(name='exam 1', finalized=False)
    exam2 = Exam(name='exam 2', finalized=True)

    db.session.add(exam1)
    db.session.add(exam2)

    problem1 = Problem(name='Problem 1', exam=exam1)
    problem2 = Problem(name='Problem 2', exam=exam2)

    db.session.add(problem1)
    db.session.add(problem2)

    problem_widget_1 = ProblemWidget(name='problem widget', problem=problem1, page=2,
                                     width=100, height=150, x=40, y=200, type='problem_widget')
    db.session.add(problem_widget_1)

    db.session.commit()
    return [(exam1, exam2), (problem1, problem2), (problem_widget_1)]


def default_mco():
    return {
        'x': 100,
        'y': 40,
        'page': 1,
        'label': 'a',
        'name': 'test'
    }


def mco_json(problem_id):
    defaults = default_mco()

    return {
        'x': defaults['x'],
        'y': defaults['y'],
        'page': defaults['page'],
        'label': defaults['label'],
        'name': defaults['name'],
        'problem_id': problem_id
    }


@pytest.fixture
def monkeypatch_write_finalized_exam(monkeypatch):
    def mock_exam_generate_data(exam):
        return None, ExamWidget(), None, None, None

    def mock_write_finalized_exam(exam):
        pass

    monkeypatch.setattr(zesje.api.exams, '_exam_generate_data', mock_exam_generate_data)
    monkeypatch.setattr(zesje.api.exams, 'write_finalized_exam', mock_write_finalized_exam)


# Actual tests


def test_not_present(test_client, add_test_data):
    result = test_client.get('/api/mult-choice/1')
    data = json.loads(result.data)

    assert data['status'] == 404


def test_problem_not_present(test_client, add_test_data):
    _, problems, _ = add_test_data
    problem_id = max(problem.id for problem in problems) + 1

    result = test_client.put('/api/mult-choice/', data=mco_json(problem_id))
    data = json.loads(result.data)

    assert data['status'] == 404


def test_add(test_client, add_test_data):
    _, problems, _ = add_test_data
    req = mco_json(problems[0].id)

    response = test_client.put('/api/mult-choice/', data=req)
    data = json.loads(response.data)

    assert data['status'] == 200


def test_add_get(test_client, add_test_data):
    _, problems, _ = add_test_data
    req = mco_json(problems[0].id)

    response = test_client.put('/api/mult-choice/', data=req)
    data = json.loads(response.data)

    assert data['mult_choice_id']

    mult_choice_id = data['mult_choice_id']
    feedback_id = data['feedback_id']

    result = test_client.get(f'/api/mult-choice/{mult_choice_id}')
    data = json.loads(result.data)

    defaults = default_mco()
    exp_resp = {
        'name': defaults['name'],
        'x': defaults['x'],
        'y': defaults['y'],
        'label': defaults['label'],
        'id': mult_choice_id,
        'type': 'mcq_widget',
        'feedback_id': feedback_id,
    }

    assert exp_resp == data


def test_update_patch(test_client, add_test_data):
    _, problems, _ = add_test_data
    req = mco_json(problems[0].id)

    response = test_client.put('/api/mult-choice/', data=req)
    data = json.loads(response.data)

    assert data['mult_choice_id']

    mult_choice_id = data['mult_choice_id']

    req2 = req.copy()
    req2['label'] = 'b'
    req2['x'] += 1
    req2['y'] += 1

    result = test_client.patch(f'/api/mult-choice/{mult_choice_id}', data=req2)
    data = json.loads(result.data)

    assert data['status'] == 200


def test_update_finalized_exam(test_client, add_test_data, monkeypatch_write_finalized_exam):
    _, problems, _ = add_test_data
    problem = problems[0]
    req = mco_json(problem.id)

    response = test_client.put('/api/mult-choice/', data=req)
    data = json.loads(response.data)

    mult_choice_id = data['mult_choice_id']

    test_client.put(f'api/exams/{problem.exam_id}', data={'finalized': 'true'})

    req2 = req.copy()
    req2['label'] = 'b'
    req2['x'] += 1
    req2['y'] += 1

    result = test_client.patch(f'/api/mult-choice/{mult_choice_id}', data=req2)
    data = json.loads(result.data)

    assert data['status'] == 405


def test_delete(test_client, add_test_data):
    _, problems, _ = add_test_data
    req = mco_json(problems[0].id)

    response = test_client.put('/api/mult-choice/', data=req)
    data = json.loads(response.data)
    mult_choice_id = data['mult_choice_id']

    response = test_client.delete(f'/api/mult-choice/{mult_choice_id}')
    data = json.loads(response.data)

    assert data['status'] == 200


def test_delete_problem_check_mco(test_client, add_test_data):
    _, problems, _ = add_test_data
    problem = problems[0]
    req = mco_json(problem.id)

    response = test_client.put('/api/mult-choice/', data=req)
    data = json.loads(response.data)
    mult_choice_id = data['mult_choice_id']

    # Delete problem
    test_client.delete(f'/api/problems/{problem.id}')

    # Get mult choice option
    response = test_client.get(f'/api/mult-choice/{mult_choice_id}')
    data = json.loads(response.data)

    assert data['status'] == 404


def test_delete_mco_check_feedback(test_client, add_test_data):
    _, problems, _ = add_test_data
    problem = problems[0]
    req = mco_json(problem.id)

    response = test_client.put('/api/mult-choice/', data=req)
    data = json.loads(response.data)
    mult_choice_id = data['mult_choice_id']

    test_client.delete(f'/api/mult-choice/{mult_choice_id}')

    # Get feedback
    response = test_client.get(f'/api/feedback/{problem.id}')
    data = json.loads(response.data)

    assert data['id']


def test_delete_not_present(test_client, add_test_data):
    response = test_client.delete('/api/mult-choice/1')
    data = json.loads(response.data)

    assert data['status'] == 404


def test_add_finalized_exam(test_client, add_test_data):
    _, problems, _ = add_test_data
    req = mco_json(problems[1].id)

    response = test_client.put('/api/mult-choice/', data=req)
    data = json.loads(response.data)

    assert data['status'] == 405


def test_delete_finalized_exam(test_client, add_test_data, monkeypatch_write_finalized_exam):
    _, problems, _ = add_test_data
    problem = problems[0]
    req = mco_json(problem.id)

    response = test_client.put('/api/mult-choice/', data=req)
    data = json.loads(response.data)

    mult_choice_id = data['mult_choice_id']

    test_client.put(f'api/exams/{problem.exam_id}', data={'finalized': 'true'})

    result = test_client.delete(f'/api/mult-choice/{mult_choice_id}')
    data = json.loads(result.data)

    assert data['status'] == 405
