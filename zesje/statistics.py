from collections import OrderedDict

from sqlalchemy.orm.exc import NoResultFound

from flask import current_app
import numpy as np
import pandas
from sqlalchemy import between, desc, func

from .database import db, Exam, Student, Grader, Solution, Submission


def solution_data(exam_id, student_id):
    """Return Python datastructures corresponding to the student submission."""

    student = Student.query.get(student_id)
    if student is None:
        raise NoResultFound(f"Student with id #{student_id} does not exist.")

    sub = Submission.query.filter(Submission.exam_id == exam_id,
                                  Submission.student_id == student_id,
                                  Submission.validated).one_or_none()
    if sub is None:
        raise RuntimeError(f'Student #{student_id} does not have a validated submission for exam {exam_id}.')

    results = []
    total_score = 0
    for solution in sub.solutions:  # Sorted by problem_id
        problem = solution.problem

        problem_data = {
            'id': problem.id,
            'name': problem.name,
            'max_score': problem.max_score
        }

        problem_data['feedback'] = [
            {'id': fo.id,
             'short': fo.text,
             'score': fo.score,
             'description': fo.description}
            for fo in solution.feedback
        ] if solution.is_graded else []

        problem_data['score'] = solution.score
        problem_data['remarks'] = solution.remarks or ''

        results.append(problem_data)

        total_score += problem_data['score'] if not np.isnan(problem_data['score']) else 0

    student = {
        'id': student.id,
        'first_name': student.first_name,
        'last_name': student.last_name,
        'email': student.email,
        'total': total_score
    }

    return student, results


def full_exam_data(exam_id):
    """Compute all grades of an exam as a pandas DataFrame."""
    exam = Exam.query.get(exam_id)
    if exam is None:
        raise NoResultFound("Exam does not exist.")

    student_ids = db.session.query(Submission.student_id)\
        .filter(Submission.exam_id == exam.id, Submission.validated)\
        .order_by(Submission.student_id)\
        .all()

    # keys used to distinguish problems or FO with the same name
    # we attach to the name its id to those that are repeated
    problem_keys = {}
    feedback_keys = {}

    columns = OrderedDict()
    columns[('First name', '')] = 'string'
    columns[('Last name', '')] = 'string'
    for problem in exam.problems:  # Sorted by problem.id
        if problem.name in problem_keys.values():
            key = f'{problem.name} ({problem.id})'
        else:
            key = problem.name
        problem_keys[problem.id] = key

        columns[(key, 'remarks')] = 'string'
        for fo in problem.root_feedback.all_descendants:
            if (key, fo.text) in feedback_keys.values():
                feedback_keys[fo.id] = (key, f'{fo.text} ({fo.id})')
            else:
                feedback_keys[fo.id] = (key, fo.text)
            columns[feedback_keys[fo.id]] = pandas.Int32Dtype()  # Contains nan
        columns[(key, 'total')] = pandas.Int32Dtype()  # Contains nan
    columns[('total', 'total')] = 'int'

    if not student_ids:
        # No students were assigned.
        return pandas.DataFrame(columns=pandas.MultiIndex.from_tuples(columns.keys()))

    df = pandas.DataFrame(
        index=pandas.Index([id for id, in student_ids], name='Student ID', dtype='int'),
        columns=pandas.MultiIndex.from_tuples(columns.keys())
    )

    for student_id, in student_ids:
        student, problems = solution_data(exam_id, student_id)

        df.loc[student['id'], ('First name', '')] = student['first_name']
        df.loc[student['id'], ('Last name', '')] = student['last_name']

        for problem in problems:
            key = problem_keys[problem['id']]

            df.loc[student['id'], (key, 'remarks')] = problem['remarks']

            for fo in problem['feedback']:
                df.loc[student['id'], feedback_keys[fo['id']]] = fo['score']

            df.loc[student['id'], (key, 'total')] = problem['score']

        df.loc[student['id'], ('total', 'total')] = student['total']

    df = df.astype(dtype=columns)  # set column types

    return df


def full_grader_data(exam_id):
    """ Compute the grader statistics for a given exam. """
    exam = Exam.query.get(exam_id)
    if exam is None:
        raise KeyError("No such exam.")

    data = []
    for problem in exam.problems:
        graders, autograded = grader_data(problem.id)

        data.append({
            "id": problem.id,
            "name": problem.name,
            "graders": graders,
            "autograded": autograded
        })

    return {"exam_id": exam_id, "exam_name": exam.name, "problems": data}


def grader_data(problem_id):
    """ Compute the grader statistics for a given problem. """
    graders = []
    autograder = current_app.config['AUTOGRADER_NAME']

    # returns a tuple with (grader id, grader name, solutions graded)
    # for each  grader that graded the given prblem ordered by grader id
    grader_results = db.session.query(Grader.id, Grader.name, func.count(Solution.grader_id))\
        .join(Solution)\
        .filter(Solution.problem_id == problem_id)\
        .group_by(Solution.grader_id)\
        .all()

    autograded_solutions = 0

    for id, name, graded in grader_results:
        if name == autograder:
            autograded_solutions = graded
            continue

        avg, total = estimate_grading_time(problem_id, id)

        graders.append({
            'id': id,
            'name': name,
            'graded': graded,
            'averageTime': avg,
            'totalTime': total
        })

    return graders, autograded_solutions


ELAPSED_TIME_BREAK = 7200   # 2 hours in seconds


def estimate_grading_time(problem_id, grader_id):
    graded_timings = get_grade_timings(problem_id, grader_id)
    if graded_timings is None:
        return 0, 0
    # since a grader might evaluate different problems at once,
    # compute the interval as the time range between the grading of the specified problem
    # and the previous problem graded
    selected_problem = graded_timings[:, 0] == problem_id
    elapsed_times = graded_timings[selected_problem, 1] - np.roll(graded_timings[:, 1], 1)[selected_problem]
    if elapsed_times[0] < 0:
        elapsed_times = elapsed_times[1:]

    # exclude very long breaks
    elapsed_times = elapsed_times[elapsed_times < ELAPSED_TIME_BREAK]
    if len(elapsed_times) == 0:
        return 0, 0

    mean, std = np.mean(elapsed_times), np.std(elapsed_times)
    # exclude longest breaks
    elapsed_times = elapsed_times[elapsed_times <= mean + std]

    # evaluate the average time in seconds excluding long breaks
    return int(np.mean(elapsed_times)), int(np.sum(elapsed_times))


def get_grade_timings(problem_id, grader_id):
    query_per_problem = Solution.query.filter(Solution.grader_id == grader_id, Solution.problem_id == problem_id)\
        .order_by(Solution.graded_at)
    first_grade, last_grade = query_per_problem[0].graded_at, query_per_problem[-1].graded_at

    if query_per_problem.count() == 1:
        # only one solution graded, then first and last grade are the same
        # look for some other graded solution before first_grade
        previous_grade = Solution.query.filter(Solution.grader_id == grader_id, Solution.graded_at < first_grade)\
            .order_by(desc(Solution.graded_at)).first()
        if previous_grade is None:
            return None

        return np.array([[previous_grade.problem_id, previous_grade.graded_at.timestamp()],
                        [problem_id, first_grade.timestamp()]])

    # get the datetime data for all Solutions graded by the same grader ordered in ascending order
    graded_timings = np.array([
        [it.problem_id, it.graded_at.timestamp()]
        for it in Solution.query
        .filter(Solution.grader_id == grader_id, between(Solution.graded_at, first_grade, last_grade))
        .order_by(Solution.graded_at)
        if it.graded_at
    ])

    return graded_timings
