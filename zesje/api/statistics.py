from math import isnan, nan
from flask_restful import Resource
import pandas as pd

from ..database import db, Exam, Submission
from ..statistics import grader_data


def scores_to_data(scores, finished):
    """ Construct the list to be send in the response sorted by total score.

    Parameters
    ----------
    scores: dict(studentID: dict(score, finished))

    Returns
    -------
    list of dict(student, score, finished)
    """
    return sorted([{
        'studentId': id,
        'score': x,
        'graded': finished[id]
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
                'averageGradingTime': 0,
                'autograded': 0,
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
            'copies': number of copies,
            'problems': list of problems data
                'id': the problem id,
                'name': them problem name,
                'max_score': maximum score of the problem,
                'results': list of scores
                    'studentId': the student id,
                    'score': the mark of the corresponding student in the problem,
                    'graded': true if there is a grader
                'extra_solutions': the amount of times a student needed an extra copy to solve this problem,
                'correlation': Rir coefficient,
                'feedback': list of feedback options
                    'id': the feedback option id,
                    'name': the feedback option name,
                    'description': the feedback option description,
                    'score': the feedback option score,
                    'used': the amount of times used,
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
                    'graded': true if the student has a grade in all problems
                'max_score': maximum score of the exam,
                'alpha': Cronbach's alpha coefficient

        """

        exam = Exam.query.get(exam_id)
        if exam is None:
            return dict(status=404, message='Exam does not exist.'), 404

        # count the total number of students as the number of validated submissions
        student_ids = db.session.query(Submission.student_id)\
            .filter(Submission.exam_id == exam.id, Submission.validated)\
            .all()

        if len(student_ids) == 0:
            # there are no vaidated submissions
            return dict(status=404, message='There are no students with a validated copy for tihs exam.'), 404

        if len(exam.problems) == 0:
            return dict(status=404, message='There are no problems for tihs exam.'), 404

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

            results = []

            for sol in p.solutions:
                student_id = sol.submission.student_id
                mark = sum(fo.score for fo in sol.feedback) if sol.feedback else nan

                if isnan(full_scores.loc[student_id, p.id]):
                    full_scores.loc[student_id, p.id] = 0
                if not isnan(mark):
                    results.append({
                        'studentId': student_id,
                        'score': mark,
                        'graded': sol.grader_id != None  # noqa: E711
                    })

                full_scores.loc[student_id, p.id] = mark

            problem_data['results'] = sorted(results, key=lambda x: x['score'])

            graders, autograded = grader_data(p.id)
            problem_data['graders'] = graders
            problem_data['autograded'] = autograded

            data[p.id] = problem_data

        # total sum per row
        full_scores.loc[:, 0] = full_scores.sum(axis=1)
        finished = full_scores.sum(axis=1, skipna=False).notna().to_dict()

        for p in exam.problems:
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

        return {
            'id': exam.id,
            'name': exam.name,
            'students': len(student_ids),
            'copies': len(exam.copies),
            'problems': [data[p.id] for p in exam.problems],
            'total': {
                'alpha': alpha,
                'max_score': total_max_score,
                'results': scores_to_data(full_scores.loc[:, 0].dropna().to_dict(), finished)
            }
        }
