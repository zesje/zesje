import pytest
from zesje.api.submissions import has_all_required_feedback
from zesje.api.submissions import _find_submission
from zesje.api.submissions import sub_to_data
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


def test_has_all_required(get_first_feedback):

    student = Student(first_name='', last_name='')
    grader = Grader(name='Zesje')
    sub = Submission(student=student, exam_id=42)
    sol = Solution(problem_id=20, submission=sub, graded_by=grader, graded_at=datetime.now())
    sol.feedback = get_first_feedback

    assert has_all_required_feedback(sol, set([1, 2]), set([3]))


def test_find_next(add_test_data, get_first_feedback, get_second_feedback):

    student = Student(first_name='', last_name='')
    student2 = Student(first_name='bob', last_name='alice')

    grader = Grader(name='Zesje')

    sub = Submission(id=25, student=student, exam_id=42)
    sub2 = Submission(id=26, student=student2, exam_id=42)

    sol = Solution(problem_id=20, submission=sub, graded_by=grader, graded_at=datetime.now())
    db.session.add(sol)
    sol2 = Solution(problem_id=20, submission=sub2, graded_by=grader, graded_at=datetime.now())

    sol.feedback = get_first_feedback
    sol2.feedback = get_second_feedback

    result = _find_submission(sub, 20, 1, 'next', False, set([3]), set([2]))
    assert result == sub_to_data(sub2)

    result2 = _find_submission(sub, 12, 1, 'next', False, set([3]), set([2]))
    assert result2[1] == 404