import pandas
from pony import orm
from collections import namedtuple, OrderedDict, ChainMap

from ..models import Exam, Problem, Student, Solution
from . import yaml_helper

def update_exam(exam, existing_yaml, new_yaml):
    existing_version, existing_name, _, existing_widgets = yaml_helper.parse(existing_yaml)
    new_version, new_name, _, new_widgets = yaml_helper.parse(new_yaml)
    if new_name != existing_name:
        raise ValueError('cannot change the exam name')
    if not all(v == 1 for v in (new_version, existing_version)):
        raise ValueError('Exam data for {} already exists, and updating it requires both the old '
                        'and new YAML to be version 1'.format(exam_name))
    if not existing_widgets.shape == new_widgets.shape:
        raise ValueError('Exam data for {} already exists, and contains a different number of '
                         'exam problems than the old version'.format(exam_name))

    new_problem_names = list(name for name in new_widgets.index
                             if name != 'studentnr')

    problems = list(Problem.select(lambda p: p.exam == exam)
                           .order_by(lambda p: p.id))
    for problem, name in zip(problems, new_problem_names):
        problem.name = name


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
            if not orm.count(problem.solutions.feedback):
                # Nobody received any grade for this problem
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
            problem_data['score'] = sum(i['score'] or 0
                                        for i in problem_data['feedback'])
            problem_data['remarks'] = '\n\n'.join(sol.remarks
                                                  for sol in solutions
                                                  if sol.remarks)
            results.append(problem_data)

        student = student.to_dict()

    student['total'] = sum(i['score'] for i in results)
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
