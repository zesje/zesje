import pytest

from zesje.database import db, Exam, Problem, ProblemWidget, Solution, Copy
from zesje.database import Submission, Scan, Page, ExamWidget, FeedbackOption, MultipleChoiceOption


def test_cascades_exam(app, exam, problem, submission, scan, exam_widget):
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


def test_cascades_problem(app, exam, problem, submission, solution, problem_widget, feedback_option):
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


def test_cascades_submission(app, exam, problem, submission, solution, copy):
    """Tests the cascades defined for a submission

    Tests the cascades for the following relations:
    - Submission -> Solution
    - Submission -> Copy
    """
    exam.problems = [problem]
    exam.submissions = [submission]

    solution.problem = problem
    solution.submission = submission
    copy.submission = submission

    db.session.add_all([exam, problem, submission])
    db.session.commit()

    assert solution in db.session
    assert copy in db.session

    db.session.delete(submission)
    db.session.commit()

    assert solution not in db.session
    assert copy not in db.session


def test_cascades_copy(app, exam, copy, page, submission):
    """Tests the cascades defined for a submission

    Tests the cascades for the following relations:
    - Copy -> Page
    - Copy -> Submission (only `save-update`, not `delete`)
    """
    exam.submissions = [submission]
    copy.submission = submission
    copy.pages = [page]

    db.session.add_all([exam, copy])
    db.session.commit()

    assert submission in db.session
    assert page in db.session

    db.session.delete(copy)
    db.session.commit()

    assert submission in db.session  # It should NOT delete the submission
    assert page not in db.session


def test_cascades_fb_mco(app, feedback_option, mc_option):
    feedback_option.mc_option = mc_option
    db.session.add(feedback_option)
    db.session.commit()

    assert mc_option in db.session

    db.session.delete(feedback_option)
    db.session.commit()

    assert mc_option not in db.session


def test_cascades_mco_fb(app, feedback_option, mc_option):
    feedback_option.mc_option = mc_option
    db.session.add(mc_option)
    db.session.commit()

    assert feedback_option in db.session

    db.session.delete(mc_option)
    db.session.commit()

    assert feedback_option not in db.session


def test_copy_exam_relationship(app, copy, submission, exam):
    db.session.add(exam)
    db.session.flush()

    submission.exam = exam

    def assert_no_relationships():
        assert copy._exam_id is None
        assert copy.exam_id is None
        assert copy.exam is None
        assert exam.copies == []

    assert_no_relationships()

    with pytest.raises(AttributeError):
        copy.exam_id = exam.id

    assert_no_relationships()

    with pytest.raises(AttributeError):
        copy.exam = exam

    assert_no_relationships()

    with pytest.raises(AttributeError):
        exam.copies = copy

    assert_no_relationships()

    copy.submission = submission
    db.session.flush()

    assert copy._exam_id == exam.id
    assert copy.exam_id == exam.id
    assert copy.exam == exam
    assert exam.copies == [copy]

    db.session.commit()


def test_copy_exam_relationship_list_no_flush(app, copy, submission, exam):
    db.session.add(exam)
    submission.exam = exam
    db.session.flush()

    submission.copies = [copy]

    assert copy._exam_id == exam.id
    assert copy.exam_id == exam.id
    assert copy.exam == exam

    db.session.commit()


def test_copy_exam_relationship_list_flush(app, copy, submission, exam):
    db.session.add(exam)
    db.session.flush()

    submission.exam = exam
    submission.copies = [copy]
    db.session.flush()

    assert copy._exam_id == exam.id
    assert copy.exam_id == exam.id
    assert copy.exam == exam

    db.session.commit()


def test_copy_exam_relationship_list_single_flush(app, copy, submission, exam):
    submission.exam = exam
    submission.copies = [copy]

    # We cannot check any ids, as nothing has been flushed yet
    assert copy.exam == exam

    db.session.commit()


def test_problem_gradable(app, exam, problem):
    problem.exam = exam
    db.session.add(exam)
    db.session.add(problem)
    db.session.commit()

    # no feedback option
    assert not problem.gradable

    problem.feedback_options.append(FeedbackOption(text='Blank', score=0))
    db.session.commit()

    # one feedback but max score is 0
    assert not problem.gradable

    problem.feedback_options.append(FeedbackOption(text='Negative', score=-1))
    db.session.commit()

    # has feedback but max score is still <= 0
    assert not problem.gradable

    problem.feedback_options.append(FeedbackOption(text='Positive', score=1))
    db.session.commit()

    # has feedback and max score is still > 0
    assert problem.gradable


def test_empty_session(app):
    # Assert no objects in session
    assert all(False for _ in db.session)


def test_empty_db(app):
    # Asesert all tables are empty
    for table in db.metadata.sorted_tables:
        assert db.session.query(table).count() == 0


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
    return Submission()


@pytest.fixture
def copy():
    return Copy(number=0)


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
