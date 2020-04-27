from math import isnan, nan
from flask_restful import Resource
from collections import defaultdict
import pandas as pd

from ..database import db, Exam, Submission, Solution
from ..statistics import grader_data
from ..pregrader import BLANK_FEEDBACK_NAME


def scores_to_data(scores):
    """ Construct the list to be send in the response sorted by score.

    Parameters
    ----------
    scores: dict(studentID: score)

    Returns
    -------
    list of dict(student, score)
    """
    return sorted([{
        'student': id,
        'score': x
    } for id, x in scores.items()], key=lambda item: item['score'])


def total_scores_to_data(scores, finished):
    """ Construct the list to be send in the response sorted by total score.

    Parameters
    ----------
    scores: dict(studentID: dict(score, finished))

    Returns
    -------
    list of dict(student, score, finished)
    """
    return sorted([{
        'student': id,
        'score': x,
        'finished': finished[id]
    } for id, x in scores.items()], key=lambda item: item['score'])


def empty_data(exam):
    return {
        'id': exam.id,
        'name': exam.name,
        'students': 0,
        'problems': [
            {
                'id': p.id,
                'name': p.name,
                'max_score': max(list(fb.score for fb in p.feedback_options) + [0]),
                'results': [],
                'correlation': None,
                'extra_solutions': 0,
                'feedback': [{
                    'id': fb.id,
                    'name': fb.text,
                    'description': fb.description,
                    'score': fb.score,
                    'used': len(fb.solutions)
                } for fb in p.feedback_options],  # Sorted by fb.id
                'graders': []
            } for p in exam.problems],
        'total': {
            'results': [],
            'max_score': sum(max(list(fb.score for fb in p.feedback_options) + [0]) for p in exam.problems),
            'alpha': None,
            'extra_copies': 0
        }
    }


class Statistics(Resource):
    """Getting a list of uploaded scans, and uploading new ones."""

    def get(self, exam_id):
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
            'problems': list of problems data
                'id': the problem id,
                'name': them problem name,
                'max_score': maximum score of the problem,
                'results': list of scores as returned by `scores_to_data`,
                'extra_solutions': the amount of times a student needed an extra copy to solve this problem,
                'correlation': Rir coefficient,
                'averageGradingTime': an estimation of the time spend grading a solution
                'feedback': list of feedback options
                    'id': the feedback option id,
                    'name': the feedback option name,
                    'description': the feedback option description,
                    'score': the feedback option score,
                    'used': the amount of times used,
                'graders': list of graders that graded this problem
                    'id': the grader id,
                    'name': the grader name,
                    'graded': the amount of solutions graded,
                    'averageTime': an estimation of the average time spend grading a solution,
                    'totalTime': an estimation of the total time spend grading all solutions,
            'total': overall results of the exam
                'results': list of total scores as returned by `scores_to_data`,
                'max_score': maximum score of the exam,
                'alpha': Cronbach's alpha coefficient,
                'extra_copies': the amount of extra copies needed compared to the total number of students

        """

        exam = Exam.query.get(exam_id)
        if exam is None:
            return dict(status=404, message='Exam does not exist.'), 404

        # count the total number of students as the number of validated submissions
        student_ids = db.session.query(Submission.student_id)\
            .filter(Submission.exam_id == exam.id, Submission.validated)\
            .all()
        if len(student_ids) == 0:
            # there are no submissions or no students have been identified
            return empty_data(exam)

        total_max_score = 0
        full_scores = pd.DataFrame(data={},
                                   index=[id for id, in student_ids],
                                   columns=[p.id for p in exam.problems] + [0],
                                   dtype=int)
        data = {}

        for p in exam.problems:
            if len(p.feedback_options) == 0:
                # exclude problems without feedback options
                continue

            max_score = max(list(fb.score for fb in p.feedback_options) + [0])
            if max_score == 0:
                continue

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
                } for fb in p.feedback_options]  # Sorted by fb.id
            }

            # add the problem score to the total
            total_max_score += max_score

            # return all solutions with the respective student id
            # for the corresponding problem that have been graded
            solutions = db.session.query(Solution, Submission.student_id)\
                                  .join(Submission)\
                                  .filter(Solution.problem_id == p.id, Submission.validated)\
                                  .all()

            sols_by_student = defaultdict(int)
            for sol, student_id in solutions:
                mark = sum(fo.score for fo in sol.feedback) if sol.feedback else nan

                if all(fo.text != BLANK_FEEDBACK_NAME for fo in sol.feedback):
                    # do not count blank solutions
                    sols_by_student[student_id] += 1

                if isnan(full_scores.loc[student_id, p.id]):
                    full_scores.loc[student_id, p.id] = 0

                full_scores.loc[student_id, p.id] += mark

            # count how many extra solutions where needed to solve this problem as
            # the total graded and non blank solutions minus the number of students
            # with at least one solution
            problem_data['extra_solutions'] = sum(list(sols_by_student.values())) - len(sols_by_student)

            problem_data['graders'] = grader_data(p.id)

            totalTime = 0
            solutionsGraded = 0
            for g in problem_data['graders']:
                if g['name'] != 'Zesje':
                    solutionsGraded += g['graded']
                    totalTime += g['totalTime']

            problem_data['averageGradingTime'] = totalTime / solutionsGraded if solutionsGraded > 0 else 0

            data[p.id] = problem_data

        # total sum per row
        full_scores.loc[:, 0] = full_scores.sum(axis=1)
        finished = full_scores.sum(axis=1, skipna=False).notna().to_dict()

        for p in exam.problems:
            data[p.id]['results'] = scores_to_data(full_scores[p.id].dropna().to_dict())
            corr = (full_scores[p.id]
                    .astype(float)
                    .corr(full_scores[0]
                          .subtract(full_scores[p.id])
                          .astype(float))
                    )
            data[p.id]['correlation'] = corr if not isnan(corr) else None

        if len(full_scores) > 2 and full_scores[0].var():
            alpha = ((len(full_scores) - 1) / (len(full_scores) - 2)
                     * (1 - full_scores.var()[:-1].sum()
                        / full_scores[0].var()))
        else:
            alpha = None

        total_extra_copies = len(exam.copies) - len(student_ids)

        return {
            'id': exam.id,
            'name': exam.name,
            'students': len(student_ids),
            'problems': [data[p.id] for p in exam.problems],
            'total': {
                'alpha': alpha,
                'max_score': total_max_score,
                'extra_copies': total_extra_copies,
                'results': total_scores_to_data(full_scores.loc[:, 0].dropna().to_dict(), finished)
            }
        }
