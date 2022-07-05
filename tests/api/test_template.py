import pytest
import json

from zesje.database import db, Exam, Student, Problem
from zesje.api.emails import template_path, default_email_template
from zesje import statistics

# test template save correctly in path

# test template render

# test email fail codes


@pytest.fixture
def mock_solution_data(monkeypatch, datadir):
    def mock_return(exam_id, student_id):
        student = {
            'id': 1,
            'first_name': 'Jane',
            'last_name': 'Doe',
            'email': 'jane.doe@fake.come',
            'total': 8
        }

        results = [{
            'id': 1,
            'name': 'name',
            'max_score': 10,
            'score': 8,
            'feedback': [],
            'remarks': ''
        }]
        return student, results
    monkeypatch.setattr(statistics, 'solution_data', mock_return)


@pytest.fixture
def app_with_data(app):
    exam = Exam(id=1, name='')
    students = [Student(id=i+1, first_name='', last_name='') for i in range(2)]
    db.session.add(exam)
    db.session.add(Problem(id=1, exam=exam, name=''))
    for student in students:
        db.session.add(student)
    db.session.commit()
    yield app


@pytest.mark.parametrize('exam_id, status', [
    (1, 200), (6, 404)
], ids=['OK', 'Invalid exam'])
def test_get_template(app_with_data, test_client, exam_id, status):
    path = template_path(1)
    assert not path.exists()
    assert not path.parent.exists()
    path.parent.mkdir()

    result = test_client.get(f'/api/templates/{exam_id}')
    print(result)
    assert result.status_code == status

    if status == 200:
        assert path.exists()

        text = json.loads(result.data)
        assert text == default_email_template


@pytest.mark.parametrize('exam_id, template, status', [
    (1, default_email_template, 200),
    (6, default_email_template, 404),
    (1, 'Not valid {% if false }', 400)
], ids=['Saved', 'Invalid exam', 'Invalid template'])
def test_save_template(app_with_data, test_client, exam_id, template, status):
    path = template_path(1)
    assert not path.exists()
    assert not path.parent.exists()
    path.parent.mkdir()

    result = test_client.put(f'/api/templates/{exam_id}', data={'template': template})
    print(result)
    assert result.status_code == status
    # template should only be saved if status code is 200
    assert path.exists() == (status == 200)


def test_render_template(app_with_data, test_client, mock_solution_data):
    test_template = (
        "{{student.first_name}} {{student.last_name}} {{student.total}}\n"
        "{% for problem in results -%}{{problem.name}} {{problem.score}} {{problem.max_score}}{% endfor %}"
    )
    result = test_client.post('/api/templates/rendered/1/1', data={'template': test_template})
    print(result)
    assert result.status_code == 200

    data = json.loads(result.data)
    student, problem = data.split('\n')

    parts = student.split(' ')
    assert parts[0] == 'Jane'
    assert parts[1] == 'Doe'
    assert int(parts[2]) == 8

    parts = problem.split(' ')
    assert parts[0] == 'name'
    assert int(parts[1]) == 8
    assert int(parts[2]) == 10
