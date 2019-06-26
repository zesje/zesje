import pytest


from zesje.database import db, Grader


@pytest.fixture
def add_test_data(app):
    with app.app_context():
        grader1 = Grader(name='grader')
        db.session.add(grader1)

        db.session.commit()


# Actual tests


def test_add_grader_no_duplicate_name(test_client, add_test_data):
    body = {'name': 'grader2'}

    result = test_client.post('/api/graders', data=body)
    assert result.status_code == 200


def test_add_grader_duplicate_name(test_client, add_test_data):
    body = {'name': 'grader'}

    result = test_client.post('/api/graders', data=body)
    assert result.status_code == 409
