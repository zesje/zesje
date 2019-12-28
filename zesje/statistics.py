from sqlalchemy.orm.exc import NoResultFound

import numpy as np
import pandas

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

        max_score = max(fb.score for fb in problem.feedback_options) or 0

        for solution in solutions:
            gid = solution.grader_id
            if not gid:
                # solution has not been graded yet
                continue

            if gid not in graders:
                grader = Grader.query.get(gid)

                graders[gid] = {
                    "grader_id": gid,
                    "grader_name": grader.name,
                    "graded": 0,
                    "avg_score": 0,
                    "max_score": 0,
                    "min_score": 0,
                    "avg_grading_time": 0
                }

            graders[gid]["graded"] += 1

            for feedback in solution.feedback:
                if feedback.score == 0:
                    graders[gid]["min_score"] += 1
                elif feedback.score == max_score:
                    graders[gid]["max_score"] += 1

                graders[gid]["avg_score"] += feedback.score

        for gid in graders.keys():
            graders[gid]["avg_score"] /= graders[gid]["graded"]
            graders[gid]["avg_grading_time"] = estimate_grading_time(problem.id, gid)

        data.append({
            "problem_id": problem.id,
            "problem_name": problem.name,
            "max_score": max_score,
            "graders": list(graders.values())
        })

    return {"exam_id": exam_id, "exam_name": exam.name, "problems": data}


ELAPSED_TIME_THRESHOLD = 3600   # 1 hour in seconds


def estimate_grading_time(problem_id, grader_id, threshold=ELAPSED_TIME_THRESHOLD):
    # get the datetime data for all Solutions graded by the same grader ordered in ascending order
    graded_timings = [
        it.graded_at.timestamp()
        for it in Solution.query.filter(Solution.problem_id == problem_id, Solution.grader_id == grader_id)
        .order_by(Solution.graded_at)
        if it.graded_at
    ]

    if len(graded_timings) < 2:
        # only one (or none) submission was graded, cannot evaluate the time spent
        return 0

    elapsed_times = np.zeros(len(graded_timings) - 1)
    for k in range(1, len(graded_timings)):
        elapsed_times[k-1] = graded_timings[k] - graded_timings[k-1]

    # evaluate the average time in seconds excluding intermediate breaks
    return int(np.mean(elapsed_times[elapsed_times < threshold]))
