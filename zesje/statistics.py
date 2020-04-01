from sqlalchemy.orm.exc import NoResultFound

import numpy as np
import pandas
from sqlalchemy import between, desc

from .database import Exam, Student, Grader, Solution


def solution_data(exam_id, student_id):
    """Return Python datastructures corresponding to the student submission."""
    exam = Exam.query.get(exam_id)
    if exam is None:
        raise NoResultFound(f"Exam with id #{exam_id} does not exist.")
    student = Student.query.get(student_id)
    if student is None:
        raise NoResultFound(f"Student with id #{student_id} does not exist.")
    if any(i is None for i in (exam, student)):
        raise RuntimeError('Student did not make a '
                           'submission for this exam')

    results = []
    for problem in exam.problems:  # Sorted by problem.id
        if not len(problem.feedback_options):
            # There is no possible feedback for this problem.
            continue
        problem_data = {
            'name': problem.name,
            'max_score': max(fb.score for fb in problem.feedback_options) or 0
        }
        # TODO Maybe replace this with an optimized query
        solutions = [sol for sols in [sub.solutions for sub in student.submissions]
                     for sol in sols
                     if sol.problem_id == problem.id]
        problem_data['feedback'] = [
            {'short': fo.text,
             'score': fo.score,
             'description': fo.description}
            for solution in solutions for fo in solution.feedback
        ]
        problem_data['score'] = (
            sum(i['score'] or 0 for i in problem_data['feedback'])
            if problem_data['feedback']
            else np.nan
        )
        problem_data['remarks'] = '\n\n'.join(sol.remarks
                                              for sol in solutions
                                              if sol.remarks)
        results.append(problem_data)

    student = {
        'id': student.id,
        'first_name': student.first_name,
        'last_name': student.last_name,
        'email': student.email,
        'total': sum(i['score'] for i in results if not np.isnan(i['score']))
    }

    return student, results


def full_exam_data(exam_id):
    """Compute all grades of an exam as a pandas DataFrame."""
    exam = Exam.query.get(exam_id)
    if exam is None:
        raise KeyError("No such exam.")
    students = sorted(sub.student.id for sub in exam.submissions if sub.student)

    data = [solution_data(exam_id, student_id)
            for student_id in students]

    if not data:
        # No students were assigned.
        columns = []
        for problem in exam.problems:  # Sorted by problem.id
            if not len(problem.feedback_options):
                # There is no possible feedback for this problem.
                continue
            for fo in problem.feedback_options:
                columns.append((problem, fo.text))
            columns.append((problem, 'total'))
        columns.append(('total', 'total'))

        result = pandas.DataFrame(columns=pandas.MultiIndex.from_tuples(columns))
        return result

    results = {}
    for student, problems in data:
        for problem in problems:
            name = problem.pop('name')
            problem[(name, 'remarks')] = problem.pop('remarks')
            for fo in problem.pop('feedback'):
                problem[(name, fo['short'])] = fo['score']
            problem[(name, 'total')] = problem.pop('score')
            problem.pop('max_score')

        results[student['id']] = {
            ('First name', ''): student['first_name'],
            ('Last name', ''): student['last_name'],
            **{
                field: entry
                for problem in problems
                for field, entry in problem.items()
            },
            ('total', 'total'): student['total']
        }

    return pandas.DataFrame(results).T


def grader_data(exam_id):
    """ Compute the grader statistics for a given exam. """
    exam = Exam.query.get(exam_id)
    if exam is None:
        raise KeyError("No such exam.")

    data = []
    for problem in exam.problems:
        solutions = problem.solutions
        graders = {}

        # max_score = max(fb.score for fb in problem.feedback_options) or 0

        for solution in solutions:
            gid = solution.grader_id
            if not gid:
                # solution has not been graded yet
                continue

            if gid not in graders:
                grader = Grader.query.get(gid)

                graders[gid] = {
                    "id": gid,
                    "name": grader.name,
                    "graded": 0,
                    # "avg_score": 0,
                    # "max_score": 0,
                    # "min_score": 0,
                    "avg_grading_time": 0,
                    "total_time": 0
                }

            graders[gid]["graded"] += 1

            '''
            for feedback in solution.feedback:
                if feedback.score == 0:
                    graders[gid]["min_score"] += 1
                elif feedback.score == max_score:
                    graders[gid]["max_score"] += 1

                graders[gid]["avg_score"] += feedback.score
            '''

        for gid in graders.keys():
            # graders[gid]["avg_score"] /= graders[gid]["graded"]
            avg, total = estimate_grading_time(problem.id, gid)
            graders[gid]["avg_grading_time"] = avg
            graders[gid]["total_time"] = total

        data.append({
            "id": problem.id,
            "name": problem.name,
            # "max_score": max_score,
            "graders": list(graders.values())
        })

    return {"exam_id": exam_id, "exam_name": exam.name, "problems": data}


ELAPSED_TIME_BREAK = 21600   # 6 hours in seconds


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
