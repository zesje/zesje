from zesje.api.submissions import _shuffle


class Submission:
    def __init__(self, id):
        self.id = id

    def __repr__(self):
        return f"submission: {self.id}"


def test_shuffle_same_grader():
    submissions = [Submission(i) for i in range(5)]

    # Assert that shuffled is the same when called twice with the same ID
    assert _shuffle(submissions, 0) == _shuffle(submissions, 0)
    # Assert that shuffled is not the same order as unshuffled, but has the same elements
    assert _shuffle(submissions, 0) != submissions and set(submissions) == set(_shuffle(submissions, 0))


def test_shuffle_different_grader():
    submissions = [Submission(i) for i in range(5)]
    # Assert that shuffled is different when called with different ID's, but has the same elements
    submissions0 = _shuffle(submissions, 0)
    submissions1 = _shuffle(submissions, 1)
    assert submissions0 != submissions1 and set(submissions0) == set(submissions1)
