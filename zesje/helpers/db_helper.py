from ..models import Problem
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
