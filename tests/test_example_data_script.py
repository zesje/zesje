import sys

sys.path.append('../')

from example_data import create_exams  # noqa E402


def test_example_data_script(test_client, app):
    exams = create_exams(app, test_client, 1, 'templated', 1, 1, 2, 0.95, 0.85, 0.9, 1, True)
    assert len(exams) == 1
    assert len(exams[0]['problems']) == 3
