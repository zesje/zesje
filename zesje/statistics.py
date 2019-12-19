from sqlalchemy.orm.exc import NoResultFound

import numpy as np
import pandas

from .database import Exam, Student, Grader


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

    data = [ ]
    for problem in exam.problems:
        solutions = problem.solutions
        prob = {
            "problem_id": problem.id,
            "max_score": max(fb.score for fb in problem.feedback_options) or 0 }
        graders = { }

        for solution in solutions:
            gid = solution.grader_id
            if not gid in graders:
                name = Grader.query.get(gid)
                graders[gid] = { 
                    "grader_name": name,
                    "graded": 0,
                    "avg_score": 0,
                    "max_score": 0,
                    "min_score": 0,
                    "first_grade_at": np.inf,
                    "last_grade_at": -1
                }
            
            graders[gid]["graded"] += 1
            if solution.graded_at:
                graded_at_in_s = int(solution.graded_at.timestamp())
                graders[gid]["first_grade_at"] = min(graders[gid]["first_grade_at"], graded_at_in_s)
                graders[gid]["last_grade_at"] = max(graders[gid]["last_grade_at"], graded_at_in_s)

            for feedback in solution.feedback_options:
                if feedback.score == 0:
                    graders[gid]["min_score"] += 1
                elif feedback.score == prob["max_score"]:
                    graders[gid]["max_score"] += 1
                
                graders[gid]["avg_score"] += feedback.score
        
        for gid in graders.keys():
            graders[gid]["avg_score"] /= graders[gid]["graded"]

            if graders[gid]["last_grade_at"] < np.inf and graders[gid]["first_grade_at"] > -1:
                graders[gid]["elapsed_time_in_sec"] = graders[gid]["last_grade_at"] - graders[gid]["first_grade_at"]
            else:
                graders[gid]["elapsed_time_in_sec"] = "NaN"
            
            del graders[gid]["last_grade_at"]
            del graders[gid]["first_grade_at"]

        prob["graders"] = graders
        data.append(prob)

    return {"exam" : exam_id, "problems": data}
