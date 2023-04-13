import pytest
from datetime import datetime

import numpy as np
from sqlalchemy.orm.exc import NoResultFound

from zesje import statistics as stats
from zesje.database import db, Exam, Problem, FeedbackOption, Student, Submission, Solution, Grader


@pytest.fixture
def add_test_data(app):
    exam = Exam(id=1, name="exam 1", finalized=True)
    db.session.add(exam)

    grader = Grader(name="Anton", oauth_id="anton")
    db.session.add(grader)

    problem1 = Problem(id=1, name="Problem", exam=exam)
    problem2 = Problem(id=2, name="Empty Problem", exam=exam)
    problem3 = Problem(id=3, name="Extra Space", exam=exam)
    db.session.add_all([problem1, problem2, problem3])
    db.session.commit()

    fo1_p1 = FeedbackOption(
        id=11, problem=problem1, text="text", description="desc", score=5, parent=problem1.root_feedback
    )
    fo1_p3 = FeedbackOption(
        id=12, problem=problem3, text="blank", description="desc", score=0, parent=problem3.root_feedback
    )
    db.session.add_all([fo1_p1, fo1_p3])

    student1 = Student(id=1000001, first_name="", last_name="")
    student2 = Student(id=1000002, first_name="", last_name="")
    student3 = Student(id=1000003, first_name="", last_name="")
    db.session.add_all([student1, student2, student3])

    sub1 = Submission(id=1, exam=exam, student=student1, copies=[], validated=True)
    db.session.add(sub1)

    sol_graded = Solution(id=1, submission=sub1, problem=problem1, graded_by=grader, graded_at=datetime.now())
    sol_graded.feedback.append(fo1_p1)
    sol_blank = Solution(id=2, submission=sub1, problem=problem3, graded_by=grader)
    sol_blank.feedback.append(fo1_p3)
    db.session.add_all([sol_graded, sol_blank, Solution(id=3, submission=sub1, problem=problem2)])

    sub2 = Submission(id=2, exam=exam, student=student2, copies=[], validated=True)
    db.session.add(sub2)

    sol_revision = Solution(id=4, submission=sub2, problem=problem1, graded_by=None)
    sol_revision.feedback.append(fo1_p1)
    db.session.add(sol_revision)

    sub3 = Submission(id=3, exam=exam, student=student3, copies=[], validated=False)
    db.session.add(sub2)

    sol_not_validated = Solution(id=5, submission=sub3, problem=problem1, graded_by=grader, graded_at=datetime.now())
    sol_not_validated.feedback.append(fo1_p1)
    db.session.add(sol_revision)

    db.session.commit()

    yield app, exam


@pytest.fixture
def add_empty_data(app):
    exam = Exam(id=1, name="exam 1", finalized=True)
    db.session.add(exam)

    problems = [Problem(id=j, name=f"Problem {j}", exam=exam) for j in range(1, 3)]
    db.session.add_all(problems)

    fo = FeedbackOption(id=1, text="Blank", score=0, problem=problems[1])
    db.session.add(fo)
    db.session.commit()

    yield app, exam


# Returns mock grader timings
@pytest.fixture
def mock_get_grade_timings(monkeypatch):
    def mock_return(problem_id, grader_id):
        if problem_id == 0:
            return np.array([[problem_id, k * 137] for k in range(8)])
        else:
            return np.array([[problem_id, k * 137 + (0 if k < 3 else 10000)] for k in range(9)])

    monkeypatch.setattr(stats, "get_grade_timings", mock_return)


def test_exam_exist(add_empty_data):
    with pytest.raises(NoResultFound):
        stats.full_exam_data(2)


def test_student_exist(add_test_data):
    with pytest.raises(NoResultFound):
        stats.solution_data(exam_id=2, student_id=1000042)


def test_submission_exist(add_test_data):
    with pytest.raises(RuntimeError):
        stats.solution_data(exam_id=2, student_id=1000001)


def test_validated_submission_exist(add_test_data):
    with pytest.raises(RuntimeError):
        stats.solution_data(exam_id=1, student_id=1000003)


def test_solution_data(add_test_data):
    student, results = stats.solution_data(exam_id=1, student_id=1000001)

    assert student["id"] == 1000001

    assert len(results) == 3

    for problem in results:
        if problem["id"] == 1:
            assert len(problem["feedback"]) == 1
            assert problem["score"] == 5
        elif problem["id"] == 2:
            assert len(problem["feedback"]) == 0
            assert np.isnan(problem["score"])
        elif problem["id"] == 3:
            assert len(problem["feedback"]) == 1
            assert problem["score"] == 0
        else:
            raise ValueError(f'Extra problem with id {problem["id"]} returned.')

    assert student["total"] == 5


def test_full_exam_data(add_test_data):
    data = stats.full_exam_data(1)

    # 11 columns = 3 problems * (1 total + 1 remarks) + 1 fbp1 + 1 fbp3 + total + 2 name
    assert data.shape == (2, 11)


# Tests whether the statistics return the correct avg and total time per problem.
# This is done with two test data, one with equal elapsed times and the other with
# a long breack inbetween that should be excluded.
@pytest.mark.parametrize("problem_id", [0, 1], ids=["Equal length", "Equal length with break"])
def test_graded_timings(mock_get_grade_timings, problem_id):
    avg, total = stats.estimate_grading_time(problem_id, 0)

    assert avg == 137

    assert total == 959
