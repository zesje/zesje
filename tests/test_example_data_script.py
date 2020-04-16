import sys

sys.path.append('../')

from example_data import create_exams  # noqa E402


def test_example_data_script(app):
    with app.test_client() as client:
        exams = create_exams(app, client, 1, 2, 1, 2, 0.95, 0.85, True)
        assert len(exams) == 1
        assert len(exams[0]['problems']) == 7
