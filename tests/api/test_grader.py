import pytest


from zesje.database import db, Grader


@pytest.fixture
def add_test_data(app):
    grader1 = Grader(oauth_id="grader@tu.nl")
    db.session.add(grader1)

    db.session.commit()


# Actual tests


@pytest.mark.parametrize(
    "grader_name, expected_status_code",
    [("grader@tu.nl", 409), ("grader2@ty.nl", 200)],
    ids=["Duplicate grader name", "Unused grader name"],
)
def test_add_grader(test_client, add_test_data, grader_name, expected_status_code):
    body = {"oauth_id": grader_name}

    result = test_client.post("/api/graders", json=body)
    assert result.status_code == expected_status_code
