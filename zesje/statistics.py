from collections import ChainMap

from pony import orm

import numpy as np
import pandas

from .database import Exam, Problem, Solution, Student


def solution_data(exam_id, student_id):
    """Return Python datastructures corresponding to the student submission."""
    with orm.db_session:
        exam = Exam[exam_id]
        student = Student[student_id]
        if any(i is None for i in (exam, student)):
            raise RuntimeError('Student did not make a '
                               'submission for this exam')

        results = []
        for problem in exam.problems.order_by(Problem.id):
            if not orm.count(problem.feedback_options):
                # There is no possible feedback for this problem.
                continue
            problem_data = {
                'name': problem.name,
                'max_score': orm.max(problem.feedback_options.score, default=0)
            }
            solutions = Solution.select(lambda s: s.problem == problem
                                        and s.submission.student == student)
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

        student = student.to_dict()

    student['total'] = sum(i['score'] for i in results if not np.isnan(i['score']))
    return student, results


def full_exam_data(exam_id):
    """Compute all grades of an exam as a pandas DataFrame."""
    with orm.db_session:
        exam = Exam[exam_id]
        if exam is None:
            raise KeyError("No such exam.")
        students = sorted(exam.submissions.student.id)

        data = [solution_data(exam_id, student_id)
                for student_id in students]

    if not data:
        # No students were assigned.
        with orm.db_session:
            columns = []
            for problem in exam.problems.order_by(Problem.id):
                if not orm.count(problem.feedback_options):
                    # There is no possible feedback for this problem.
                    continue
                for fo in problem.feedback_options.text:
                    columns.append((problem, fo))
                columns.append((problem, 'total'))
            columns.append(('total', 'total'))

        result = pandas.DataFrame(columns=pandas.MultiIndex.from_tuples(columns))
        return result

    students = pandas.DataFrame({i[0]['id']: i[0] for i in data}).T
    del students['id']

    results = {}
    for result in data:
        for problem in result[1]:
            name = problem.pop('name')
            problem[(name, 'remarks')] = problem.pop('remarks')
            for fo in problem.pop('feedback'):
                problem[(name, fo['short'])] = fo['score']
            problem[(name, 'total')] = problem.pop('score')
            problem.pop('max_score')
        results[result[0]['id']] = dict(ChainMap({('total', 'total'):
                                                  result[0]['total']},
                                                 *result[1]))

    return pandas.DataFrame(results).T
