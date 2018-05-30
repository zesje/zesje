import random

import pytest

from zesje.models import Exam, _generate_exam_token


# I couldn't figure out how to make the mock return True on the first call and False on the second call. Therefore,
# I just used randomness and run the test 50 times to make sure that that scenario occurs.
@pytest.mark.parametrize('execution_number', range(50))
def test_exam_generate_token_length_uppercase(execution_number, monkeypatch):
    def mock_select_return(f):
        class MockQuery:
            def exists():
                return random.choice([True, False])
        return MockQuery

    monkeypatch.setattr(Exam, 'select', mock_select_return)

    id = _generate_exam_token()
    assert len(id) == 12
    assert id.isupper()
