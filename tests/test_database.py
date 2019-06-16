import pytest
from flask import Flask

from zesje.database import db, _generate_exam_token, Exam, Problem, ProblemWidget, Solution
from zesje.database import Submission, Scan, Page, ExamWidget, FeedbackOption, MultipleChoiceOption


@pytest.mark.parametrize('duplicate_count', [
    0, 1],
    ids=['No existing token', 'Existing token'])
def test_exam_generate_token_length_uppercase(duplicate_count, monkeypatch):
    class MockQuery:
        def __init__(self):
            self.duplicates = duplicate_count + 1

        def filter(self, *args):
            return self

        def first(self):
            self.duplicates -= 1
            return None if self.duplicates else True

    app = Flask(__name__, static_folder=None)
    app.config.update(
        SQLALCHEMY_DATABASE_URI='sqlite:///:memory:',
        SQLALCHEMY_TRACK_MODIFICATIONS=False  # Suppress future deprecation warning
    )
    db.init_app(app)

    with app.app_context():
        monkeypatch.setattr(Exam, 'query', MockQuery())

        id = _generate_exam_token()
        assert len(id) == 12
        assert id.isupper()


def test_cascades_exam(empty_app, exam, problem, submission, scan, exam_widget):
    """Tests the cascades defined for an exam

    Tests the cascades for the following relations:
    - Exam -> Submission
    - Exam -> Problem
    - Exam -> Scan
    - Exam -> ExamWidget
    """
    empty_app.app_context().push()
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
    empty_app.app_context().push()

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
    empty_app.app_context().push()

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
    empty_app.app_context().push()

    feedback_option.mc_option = mc_option
    db.session.add(feedback_option)
    db.session.commit()

    assert mc_option in db.session

    db.session.delete(feedback_option)
    db.session.commit()

    assert mc_option not in db.session


def test_cascades_mco_fb(empty_app, feedback_option, mc_option):
    empty_app.app_context().push()

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
