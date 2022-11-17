import pytest
import os

from flask import json
from zesje.database import db, Exam, Problem, ProblemWidget, Submission, ExamLayout
from zesje.api.exams import generate_exam_token


@pytest.fixture
def add_test_data(app):
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
def test_add_templated_exam(datadir, test_client):
    with open(os.path.join(datadir, 'blank-a4-2pages.pdf'), 'rb') as pdf:
        response = test_client.post('/api/exams',
                                    data={'exam_name': 'The Exam', 'pdf': pdf, 'layout': ExamLayout.templated.name})

        assert response.status_code == 200

    response = test_client.get('/api/exams')
    data = response.get_json()

    assert len(data) == 1

    assert data[0]['layout'] == ExamLayout.templated.name


def test_add_templated_exam_without_pdf(datadir, test_client):
    response = test_client.post('/api/exams',
                                data={'exam_name': 'The Exam', 'layout': ExamLayout.templated.name})

    assert response.status_code == 400


def test_add_unstructured_exam(test_client):
    response = test_client.post('/api/exams',
                                data={'exam_name': 'The Exam', 'layout': ExamLayout.unstructured.name})
    assert response.status_code == 200

    response = test_client.get('/api/exams')
    data = response.get_json()

    assert len(data) == 1

    assert data[0]['layout'] == ExamLayout.unstructured.name


def test_add_exam_invalid_layout(test_client):
    response = test_client.post('/api/exams',
                                data={'exam_name': 'The Exam', 'layout': -1})

    assert response.status_code == 422


@pytest.mark.parametrize(
    'name, status_code',
    [('New name', 200), ('', 422)],
    ids=['New name', 'Empty'])
def test_change_exam_name(test_client, add_test_data, name, status_code):
    response = test_client.patch('/api/exams/1', json={'name': name})

    assert response.status_code == status_code

    if status_code == 200:
        data = test_client.get('/api/exams/1').get_json()
        assert data['name'] == name


def test_get_exams_mult_choice(test_client, add_test_data):
    mc_option_1 = {
        'x': 100,
        'y': 40,
        'problem_id': 1,
        'label': 'a',
        'name': 'test'
    }
    test_client.put('/api/mult-choice/', json=mc_option_1)

    mc_option_2 = {
        'x': 100,
        'y': 40,
        'problem_id': 1,
        'label': 'a',
        'name': 'test'
    }
    test_client.put('/api/mult-choice/', json=mc_option_2)

    response = test_client.get('/api/exams/1')
    data = json.loads(response.data)

    assert len(data['problems'][0]['mc_options']) == 2


@pytest.mark.parametrize('ids, names, pdfs, tokens_equal', [
    ([0, 0], ['Final', 'Final'], [b'EXAM PDF DATA', b'EXAM PDF DATA'], True),
    ([0, 1], ['Final', 'Final'], [b'EXAM PDF DATA', b'EXAM PDF DATA'], False),
    ([0, 0], ['Final', 'Midterm'], [b'EXAM PDF DATA', b'EXAM PDF DATA'], False),
    ([0, 0], ['Final', 'Final'], [b'EXAM PDF DATA', b'DIFFERENT PDF DATA'], False),
], ids=['Same everything', 'Different ids', 'Different names', 'Different pdfs'])
def test_exam_generate_token_same(ids, names, pdfs, tokens_equal):
    token_a = generate_exam_token(ids[0], names[0], pdfs[0])
    token_b = generate_exam_token(ids[1], names[1], pdfs[1])

    assert len(token_a) == len(token_b) == 12
    assert (token_a == token_b) is tokens_equal


@pytest.mark.parametrize(
    'no_with_subs, no_without_subs',
    [(0, 0), (0, 1), (1, 0), (1, 1), (5, 10)],
    ids=['No exams', 'Without submissions', 'With submissions', 'Mixed', 'Many'])
def test_get_exams(test_client, no_with_subs, no_without_subs):
    for i in range(no_without_subs):
        db.session.add(Exam(name=f'No Submissions {i}'))

    for i in range(no_with_subs):
        exam = Exam(name=f'Submissions {i}')
        db.session.add(exam)
        for _ in range(i):
            db.session.add(Submission(exam=exam))

    db.session.commit()

    response = test_client.get('/api/exams')

    assert response.status_code == 200

    data = json.loads(response.data)
    exams = {exam['name']: exam['submissions'] for exam in data}

    assert len(exams) == no_with_subs + no_without_subs

    for i in range(no_without_subs):
        exam_name = f'No Submissions {i}'
        assert exam_name in exams
        assert exams[exam_name] == 0

    for i in range(no_with_subs):
        exam_name = f'Submissions {i}'
        assert exam_name in exams
        assert exams[exam_name] == i


@pytest.mark.parametrize(
    'finalized, status_code',
    [(False, 200), (True, 409)],
    ids=['Not finalized', 'Finalized'])
def test_delete_exam(test_client, finalized, status_code):
    exam = Exam(name='finalized', finalized=finalized)
    db.session.add(exam)
    db.session.commit()

    response = test_client.delete(f'/api/exams/{exam.id}')

    assert response.status_code == status_code

    response = test_client.get('/api/exams')
    data = response.get_json()

    assert len(data) == (1 if finalized else 0)


def test_unfinalize_exam(test_client):
    exam = Exam(name='finalized', finalized=True)
    db.session.add(exam)
    db.session.commit()

    response = test_client.put(f'/api/exams/{exam.id}', json={'finalized': False})
    assert response.status_code == 409
    assert exam.finalized
