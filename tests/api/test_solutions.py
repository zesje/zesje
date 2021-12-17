import pytest
from zesje.database import db, Exam, Problem, FeedbackOption,\
                           Student, Submission, Solution, Grader


@pytest.fixture
def add_test_data(app):
    exam = Exam(id=1, name='exam', finalized=True, layout="unstructured")
    db.session.add(exam)

    problem = Problem(id=1, name='Problem', exam=exam)
    db.session.add(problem)

    student = Student(id=1, first_name='Harry', last_name='Lewis')
    db.session.add(student)

    grader = Grader(id=1, name='Zesje', oauth_id='Zesje')
    db.session.add(grader)

    sub = Submission(id=1, student=student, exam=exam)
    db.session.add(sub)

    sol = Solution(id=1, submission=sub, problem=problem)
    db.session.add(sol)
    db.session.commit()

    root = problem.root_feedback

    for i in range(2):
        fo_parent = FeedbackOption(id=i + 1,
                                   problem=problem,
                                   text=chr(i + 65),
                                   description='',
                                   score=i,
                                   parent=root)
        db.session.add(fo_parent)
        db.session.commit()
        for j in range(1, 3):
            fo = FeedbackOption(id=(i + 1) * 10 + j,
                                problem=problem,
                                text=chr(i + 65) + chr(j + 65),
                                description='',
                                score=-1 * i * j,
                                parent_id=i + 1)
            db.session.add(fo)

    db.session.commit()

    yield app


def test_get_solution(test_client, add_test_data):
    res = test_client.get('/api/solution/1/1/1')
    assert res.status_code == 200

    # exam does not exist
    res = test_client.get('/api/solution/18428/1/1')
    assert res.status_code == 404

    # submission does not exist
    res = test_client.get('/api/solution/1/965/1')
    assert res.status_code == 404

    # no solution for this problem id
    res = test_client.get('/api/solution/1/1/87841')
    assert res.status_code == 404

    db.session.add(Exam(id=2, name='exam2', finalized=True, layout="unstructured"))
    # exam exist but submission does not belong to it
    res = test_client.get('/api/solution/2/1/1')
    assert res.status_code == 400


def test_add_remark(test_client, add_test_data, monkeypatch_current_user):
    remark = 'this is a remark'
    res = test_client.post('/api/solution/1/1/1', data={
        'remark': remark
    })

    assert res.status_code == 200

    res = test_client.get('/api/solution/1/1/1')
    solution = res.get_json()

    assert not solution['gradedBy']
    assert solution['remarks'] == remark


def test_toggle_feedback(test_client, add_test_data, monkeypatch_current_user):
    # toogle parent
    for j in range(2):
        res = test_client.put('/api/solution/1/1/1', data={
            'id': 1
        })

        assert res.status_code == 200
        assert res.get_json()['state'] == (j % 2 == 0)

    # toogle child
    for j in range(2):
        res = test_client.put('/api/solution/1/1/1', data={
            'id': 2 * 10 + 2
        })
        assert res.status_code == 200
        checked = res.get_json()['state']
        assert checked == (j % 2 == 0)

        res = test_client.get('/api/solution/1/1/1')
        checked_feedback = res.get_json()['feedback']
        if checked:
            assert 2 in checked_feedback
            assert (2 * 10 + 2) in checked_feedback
        else:
            assert 2 in checked_feedback

    # toogle other child of same parent
    res = test_client.put('/api/solution/1/1/1', data={
        'id': 2 * 10 + 1
    })
    assert res.status_code == 200
    checked = res.get_json()['state']
    assert checked

    res = test_client.get('/api/solution/1/1/1')
    checked_feedback = res.get_json()['feedback']
    assert 2 in checked_feedback
    assert (2 * 10 + 1) in checked_feedback

    # uncheck parent
    res = test_client.put('/api/solution/1/1/1', data={
        'id': 2
    })
    assert res.status_code == 200
    checked = res.get_json()['state']
    assert not checked

    res = test_client.get('/api/solution/1/1/1')
    checked_feedback = res.get_json()['feedback']
    assert not checked_feedback


def test_approve(test_client, add_test_data, monkeypatch_current_user):
    res = test_client.put('/api/solution/approve/1/1/1', data={
        'approve': 1
    })

    # no feedback selected
    assert res.status_code == 409

    res = test_client.put('/api/solution/1/1/1', data={
        'id': 1
    })

    # toogle approve
    for j in range(2):
        res = test_client.put('/api/solution/approve/1/1/1', data={
            'approve': j == 0
        })

        assert res.status_code == 200
        approved = res.get_json()['state']
        assert approved == (j == 0)

        res = test_client.get('/api/solution/1/1/1')
        graded_by = res.get_json()['gradedBy']
        if approved:
            assert graded_by['id'] == 1
        else:
            assert graded_by is None