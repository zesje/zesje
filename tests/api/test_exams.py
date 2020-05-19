import pytest

from flask import json
from zesje.database import db, Exam, Problem, ProblemWidget, Submission, ExamType
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


def test_get_exams_mult_choice(test_client, add_test_data):
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


def test_exam_types(test_client):
    response = test_client.get('/api/exams/types')

    assert response.status_code == 200

    data = json.loads(response.data)

    assert len(list(ExamType)) == len(data)
