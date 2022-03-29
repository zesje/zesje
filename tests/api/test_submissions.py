import pytest
from zesje.api.submissions import has_all_required_feedback, _find_submission, find_number_of_matches
from datetime import datetime
from zesje.database import db, Exam, Problem, FeedbackOption,\
                           Student, Submission, Solution, Grader


@pytest.fixture
def add_test_data(app):
    exam = Exam(id=42, name='exam f', finalized=True, layout="unstructured")
    db.session.add(exam)

    problem = Problem(id=20, name='Problem sad', exam_id=42)
    db.session.add(problem)
    db.session.commit()
    yield app


@pytest.fixture
def get_first_feedback():
    feedback_option1 = FeedbackOption(id=1, problem_id=20, text='text', description='desc', score=1)
    feedback_option2 = FeedbackOption(id=2, problem_id=20, text='text', description='desc', score=1)
    return [feedback_option1, feedback_option2]


@pytest.fixture
def get_second_feedback():
    feedback_option3 = FeedbackOption(id=3, problem_id=20, text='text', description='desc', score=1)
    return [feedback_option3]


@pytest.fixture
def add_test_submissions(app):
    student = Student(first_name='Harry', last_name='Lewis')
    student2 = Student(first_name='bob', last_name='alice')
    student3 = Student(first_name='Charlie', last_name='Bob')

    grader = Grader(id=1, name='Zesje', oauth_id='Zesje')
    grader2 = Grader(id=2, name='Alice', oauth_id='Smith')

    sub = Submission(id=25, student=student, exam_id=42)
    sub2 = Submission(id=26, student=student2, exam_id=42)
    sub3 = Submission(id=27, student=student3, exam_id=42)

    sol = Solution(problem_id=20, submission=sub, graded_by=grader, graded_at=datetime.now())
    db.session.add(sol)
    sol2 = Solution(problem_id=20, submission=sub2, graded_by=grader2, graded_at=datetime.now())
    db.session.add(sol2)
    sol3 = Solution(problem_id=20, submission=sub3, graded_by=grader2, graded_at=datetime.now())
    db.session.add(sol3)
    yield app


def test_has_all_required(get_first_feedback):
    student = Student(first_name='', last_name='')
    grader = Grader(name='Zesje', oauth_id='Zesje')
    sub = Submission(student=student, exam_id=42)
    sol = Solution(problem_id=20, submission=sub, graded_by=grader, graded_at=datetime.now())
    sol.feedback = get_first_feedback

    assert has_all_required_feedback(sol, set([1, 2]), set([3]))


def test_find_next(add_test_data, get_first_feedback, get_second_feedback):
    student = Student(first_name='', last_name='')
    student2 = Student(first_name='bob', last_name='alice')

    grader = Grader(name='Zesje', oauth_id='Zesje')

    sub = Submission(id=25, student=student, exam_id=42)
    sub2 = Submission(id=26, student=student2, exam_id=42)

    sol = Solution(problem_id=20, submission=sub, graded_by=grader, graded_at=datetime.now())
    db.session.add(sol)
    sol2 = Solution(problem_id=20, submission=sub2, graded_by=grader, graded_at=datetime.now())
    db.session.add(sol2)

    sol.feedback = get_first_feedback
    sol2.feedback = get_second_feedback

    result, *_ = _find_submission(sub, Problem.query.get(20), 1, 'next', False, set([3]), set([2]), None)
    assert result == sub2


def test_find_next_graded_by(add_test_data):
    student = Student(first_name='', last_name='')
    student2 = Student(first_name='bob', last_name='alice')

    grader = Grader(id=1, name='Zesje', oauth_id='Zesje')
    grader2 = Grader(id=2, name='Alice', oauth_id='Smith')

    sub = Submission(id=25, student=student, exam_id=42)
    sub2 = Submission(id=26, student=student2, exam_id=42)

    sol = Solution(problem_id=20, submission=sub, graded_by=grader, graded_at=datetime.now())
    db.session.add(sol)
    sol2 = Solution(problem_id=20, submission=sub2, graded_by=grader2, graded_at=datetime.now())
    db.session.add(sol2)

    result, *_ = _find_submission(sub, Problem.query.get(20), 1, 'next', False, set(), set(), 2)
    assert result == sub2


def test_find_length(add_test_data, get_first_feedback, get_second_feedback):
    student = Student(first_name='Harry', last_name='Lewis')
    student2 = Student(first_name='bob', last_name='alice')
    student3 = Student(first_name='Charlie', last_name='Bob')

    grader = Grader(id=1, name='Zesje', oauth_id='Zesje')
    grader2 = Grader(id=2, name='Alice', oauth_id='Smith')

    sub = Submission(id=25, student=student, exam_id=42)
    sub2 = Submission(id=26, student=student2, exam_id=42)
    sub3 = Submission(id=27, student=student3, exam_id=42)

    sol = Solution(problem_id=20, submission=sub, graded_by=grader, graded_at=datetime.now())
    db.session.add(sol)
    sol2 = Solution(problem_id=20, submission=sub2, graded_by=grader2, graded_at=datetime.now())
    db.session.add(sol2)
    sol3 = Solution(problem_id=20, submission=sub3, graded_by=grader2, graded_at=datetime.now())
    db.session.add(sol3)

    sol.feedback = get_first_feedback
    sol2.feedback = get_second_feedback
    sol3.feedback = get_first_feedback

    result = find_number_of_matches(Problem.query.get(20), False, [1], [], 2)
    assert result == 1


def test_get_all_submissions(test_client, add_test_data, add_test_submissions):
    res = test_client.get('/api/submissions/42')
    data = res.get_json()
    assert len(data) == 3


def test_exam_not_found(test_client, add_test_data, add_test_submissions):
    res = test_client.get('/api/submissions/43')
    assert res.status_code == 404


def test_submission_not_found(test_client, add_test_data, add_test_submissions):
    res = test_client.get('/api/submissions/42/404')
    assert res.status_code == 404


def test_problem_not_found(test_client, add_test_data, add_test_submissions):
    res = test_client.get('/api/submissions/42/25?problem_id=102')
    assert res.status_code == 404


def test_submission_from_different_exam(test_client, add_test_data, add_test_submissions):
    exam = Exam(id=43, name='exam g', finalized=True, layout="unstructured")
    db.session.add(exam)
    problem = Problem(id=21, name='Problem sadder', exam_id=43)
    db.session.add(problem)

    res = test_client.get('/api/submissions/43/25')
    assert res.status_code == 400


def test_get_submission(test_client, add_test_data, add_test_submissions, monkeypatch_current_user):
    res = test_client.get('/api/submissions/42/25?problem_id=20&direction=next')
    data = res.get_json()
    assert data['meta']['filter_matches'] == 3
    assert data['meta']['n_graded'] == 3
    assert data['id'] == 27
