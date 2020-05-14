import pytest
import numpy as np
from zesje import statistics as stats

# Tests


# Returns mock grader timings
@pytest.fixture
def mock_get_grade_timings(monkeypatch):
    def mock_return(problem_id, grader_id):
        if problem_id == 0:
            return np.array([[problem_id, k * 137] for k in range(8)])
        else:
            return np.array([[problem_id, k * 137 + (0 if k < 3 else 10000)] for k in range(9)])
    monkeypatch.setattr(stats, 'get_grade_timings', mock_return)


# Tests whether the statistics return the correct avg and total time per problem.
# This is done with two test data, one with equal elapsed times and the other with
# a long breack inbetween that should be excluded.
@pytest.mark.parametrize('problem_id', [0, 1], ids=['Equal length', 'Equal length with break'])
def test_graded_timings(mock_get_grade_timings, problem_id):
    avg, total = stats.estimate_grading_time(problem_id, 0)

    assert avg == 137

    assert total == 959
