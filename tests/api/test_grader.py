import pytest


from zesje.database import db, Grader


@pytest.fixture
def add_test_data(app):
    with app.app_context():
        grader1 = Grader(name='grader')
        db.session.add(grader1)

        db.session.commit()


# Actual tests


@pytest.mark.parametrize('grader_name, expected_status_code', [
    ('grader', 409),
    ('grader2', 200)],
    ids=['Duplicate grader name', 'Unused grader name'])
def test_add_grader(test_client, add_test_data, grader_name, expected_status_code):
    body = {'name': grader_name}

    result = test_client.post('/api/graders', data=body)
    assert result.status_code == expected_status_code