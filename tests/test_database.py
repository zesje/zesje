import pytest

from zesje.database import db, Exam, Problem, ProblemWidget, Solution
from zesje.database import Submission, Scan, Page, ExamWidget, FeedbackOption, MultipleChoiceOption


@pytest.fixture
def empty_app(db_app):
    with db_app.app_context():
        db.drop_all()
        db.create_all()
        yield db_app


def test_mysql_server(mysql_proc):
    """Check if mysql server is running"""
    assert mysql_proc.running()


def test_cascades_exam(empty_app, exam, problem, submission, scan, exam_widget):
    """Tests the cascades defined for an exam

    Tests the cascades for the following relations:
    - Exam -> Submission
    - Exam -> Problem
    - Exam -> Scan
    - Exam -> ExamWidget
    """
    exam.problems = [problem]
    exam.scans = [scan]
    exam.submissions = [submission]
    exam.widgets = [exam_widget]

    db.session.add(exam)
    db.session.commit()

    assert problem in db.session
    assert submission in db.session
    assert scan in db.session
    assert exam_widget in db.session

    db.session.delete(exam)
    db.session.commit()

    assert problem not in db.session
    assert submission not in db.session
    assert scan not in db.session
    assert exam_widget not in db.session


def test_cascades_problem(empty_app, exam, problem, submission, solution, problem_widget, feedback_option):
    """Tests the cascades defined for a problem

    Tests the cascades for the following relations:
    - Problem -> Solution
    - Problem -> ProblemWidget
    - Problem -> FeedbackOption
    """
    exam.problems = [problem]
    exam.submissions = [submission]
    solution.submission = submission
    problem.widget = problem_widget
    problem.solutions = [solution]
    problem.feedback_options = [feedback_option]

    db.session.add_all([exam, problem, submission])
    db.session.commit()

    assert solution in db.session
    assert problem_widget in db.session
    assert feedback_option in db.session

    db.session.delete(problem)
    db.session.commit()

    assert solution not in db.session
    assert problem_widget not in db.session
    assert feedback_option not in db.session


def test_cascades_submission(empty_app, exam, problem, submission, solution, page):
    """Tests the cascades defined for a submission

    Tests the cascades for the following relations:
    - Submission -> Solution
    - Submission -> Page
    """
    exam.problems = [problem]
    exam.submissions = [submission]

    solution.problem = problem
    solution.submission = submission
    page.submission = submission

    db.session.add_all([exam, problem, submission])
    db.session.commit()

    assert solution in db.session
    assert page in db.session

    db.session.delete(submission)
    db.session.commit()

    assert solution not in db.session
    assert page not in db.session


def test_cascades_fb_mco(empty_app, feedback_option, mc_option):
    feedback_option.mc_option = mc_option
    db.session.add(feedback_option)
    db.session.commit()

    assert mc_option in db.session

    db.session.delete(feedback_option)
    db.session.commit()

    assert mc_option not in db.session


def test_cascades_mco_fb(empty_app, feedback_option, mc_option):
    feedback_option.mc_option = mc_option
    db.session.add(mc_option)
    db.session.commit()

    assert feedback_option in db.session

    db.session.delete(mc_option)
    db.session.commit()

    assert feedback_option not in db.session


@pytest.fixture
def mc_option():
    return MultipleChoiceOption(name='', x=0, y=0)


@pytest.fixture
def exam():
    return Exam(name='')


@pytest.fixture
def problem():
    return Problem(name='')


@pytest.fixture
def problem_widget():
    return ProblemWidget(name='', page=0, x=0, y=0, width=0, height=0)


@pytest.fixture
def exam_widget():
    return ExamWidget(name='', x=0, y=0)


@pytest.fixture
def submission():
    return Submission(copy_number=0)


@pytest.fixture
def solution():
    return Solution()


@pytest.fixture
def scan():
    return Scan(name='', status='')


@pytest.fixture
def page():
    return Page(path='', number=0)


@pytest.fixture
def feedback_option():
    return FeedbackOption(text='')
