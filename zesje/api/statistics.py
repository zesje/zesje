from math import isnan, nan

from flask.views import MethodView
import pandas as pd

from ._helpers import DBModel, use_kwargs
from ..database import db, Exam, Submission, ExamLayout
from ..statistics import grader_data


class Statistics(MethodView):
    """Getting a list of uploaded scans, and uploading new ones."""

    @use_kwargs({'exam': DBModel(Exam, required=True)})
    def get(self, exam):
        """get statistics for a particular exam.

        Parameters
        ----------
        exam_id : int

        Returns
        -------
        dict with exam data:
            'id': the exam id,
            'name': the exam name,
            'students': number of students that did the exam,
            'copies': number of copies,
            'problems': list of problems data
                'id': the problem id,
                'name': them problem name,
                'max_score': maximum score of the problem,
                'results': list of scores
                    'studentId': the student id,
                    'score': the mark of the corresponding student in the problem,
                    'graded': true if there is a grader,
                'mean': dictionary containing,
                    'value': the mean value,
                    'error': the standard deviation,
                'correlation': Rir coefficient,
                'feedback': list of feedback options
                    'id': the feedback option id,
                    'name': the feedback option name,
                    'description': the feedback option description,
                    'score': the feedback option score,
                    'used': the amount of times used,
                'inRevision': the amount of solutions with a grade but no grader, those set aside,
                'autograded': the amount of solutions graded by Zesje,
                'graders': list of graders that graded this problem
                    'id': the grader id,
                    'name': the grader name,
                    'graded': the amount of solutions graded,
                    'averageTime': an estimation of the average time spend grading a solution,
                    'totalTime': an estimation of the total time spend grading all solutions,
            'total': overall results of the exam
                'results': list of total scores
                    'studentId': the student id,
                    'score': the total score for this student,
                    'ungraded': number of ungraded problems
                'max_score': maximum score of the exam,
                'alpha': Cronbach's alpha coefficient,
                'mean': dictionary containing,
                    'value': the mean value,
                    'error': the standard deviation,

        """
        # count the total number of students as the number of validated submissions
        student_ids = db.session.query(Submission.student_id)\
            .filter(Submission.exam_id == exam.id, Submission.validated)\
            .all()

        if len(student_ids) == 0:
            return dict(status=404, message='There are no students with a validated copy for this exam.'), 404

        total_max_score = 0
        full_scores = pd.DataFrame(data={},
                                   index=[id for id, in student_ids],
                                   columns=[p.id for p in exam.problems if p.gradable] + [0],
                                   dtype=int)
        ungraded = full_scores.copy()
        data = []

        for p in exam.problems:
            if not p.gradable:
                # exclude problems without feedback options
                continue

            max_score = p.max_score

            problem_data = {
                'id': p.id,
                'name': p.name,
                'max_score': max_score,
                'feedback': [{
                    'id': fb.id,
                    'name': fb.text,
                    'description': fb.description,
                    'score': fb.score,
                    'used': len(fb.solutions)
                } for fb in p.feedback_options if fb.parent_id is not None]  # Sorted by fb.id
            }

            # add the problem score to the total
            total_max_score += max_score

            results = []
            in_revision = 0

            for sol in p.solutions:
                if not sol.submission.validated:
                    continue

                student_id = sol.submission.student_id
                mark = sol.score

                if not isnan(mark):
                    if not (is_graded := sol.is_graded):
                        in_revision += 1
                        ungraded.loc[student_id, p.id] = 1

                    results.append({
                        'studentId': student_id,
                        'score': mark,
                        'graded': is_graded
                    })

                    full_scores.loc[student_id, p.id] = mark
                else:
                    ungraded.loc[student_id, p.id] = 1

            problem_data['results'] = sorted(results, key=lambda x: x['score'])
            problem_data['inRevision'] = in_revision

            graders, autograded = grader_data(p.id)
            problem_data['graders'] = graders
            problem_data['autograded'] = autograded

            problem_data['mean'] = {
                'value': full_scores.loc[:, p.id].mean() if len(results) >= 1 else 0,
                'error': full_scores.loc[:, p.id].std() if len(results) > 1 else 0
            }

            data.append(problem_data)

        full_scores.loc[:, 0] = full_scores.sum(axis=1)

        # counts the number of ungraded problems per student
        problems_ungraded = ungraded.sum(axis=1)

        # list with total score and number of ungraded problems by student
        total_results = sorted([{
            'studentId': id,
            'score': full_scores.loc[id, 0],
            'ungraded': int(problems_ungraded.loc[id])
        } for id, in student_ids], key=lambda item: item['score'])

        total_mean = {
            'value': full_scores.loc[:, 0].mean() if len(total_results) >= 1 else 0,
            'error': full_scores.loc[:, 0].std() if len(total_results) > 1 else 0
        }

        for j in range(len(data)):
            id = data[j]['id']
            corr = (full_scores[id]
                    .astype(float)
                    .corr(full_scores[0]
                          .subtract(full_scores[id])
                          .astype(float))
                    ) if len(student_ids) > 2 else nan
            data[j]['correlation'] = corr if not isnan(corr) else None

        if len(total_results) > 2 and full_scores[0].var():
            alpha = ((len(full_scores) - 1) / (len(full_scores) - 2)
                     * (1 - full_scores.var().iloc[:-1].sum()
                        / full_scores[0].var()))
        else:
            alpha = None

        return {
            'id': exam.id,
            'name': exam.name,
            'students': len(student_ids),
            'copies': len(exam.copies) if exam.layout == ExamLayout.templated else len(student_ids),
            'problems': data,
            'total': {
                'alpha': alpha,
                'max_score': total_max_score,
                'results': total_results,
                'mean': total_mean
            }
        }
