from math import isnan, nan
from flask_restful import Resource
from collections import defaultdict
import pandas as pd
from sqlalchemy import func

from ..database import db, Exam, Submission, Solution
from ..statistics import grader_data


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
                'scores': [],
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
            'scores': [],
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
                'scores': list of scores as returned by `scores_to_data`,
                'extra_solutions': the amount of times a student needed an extra copy to solve this problem,
                'correlation': Rir coefficient,
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
                    'avg_grading_time': an estimate of the average time spend grading,
                    'total_grading_time': an estimate of the total time spend grading,
            'total': overall results of the exam
                'scores': list of total scores as returned by `scores_to_data`,
                'max_score': maximum score of the exam,
                'alpha': Cronbach's alpha coefficient,
                'extra_copies': the amount of extra copies needed compared to the total number of students

        """

        exam = Exam.query.get(exam_id)
        if exam is None:
            return dict(status=404, message='Exam does not exist.'), 404

        # count the total number of students as the number of submissions for this exam
        # with a different and not null student id
        students = db.session.query(func.count(Submission.student_id))\
            .filter(Submission.exam_id == exam.id, Submission.student_id != None)\
            .scalar() # noqa E711

        if students == 0:
            # there are no submissions or no students have been identified
            return empty_data(exam)

        data = {0: {  # total
            'scores': defaultdict(int),
            'max_score': 0
            }
        }

        for p in exam.problems:
            problem_data = {
                'id': p.id,
                'name': p.name,
                'max_score': max(list(fb.score for fb in p.feedback_options) + [0]),
                'feedback': [{
                    'id': fb.id,
                    'name': fb.text,
                    'description': fb.description,
                    'score': fb.score,
                    'used': len(fb.solutions)
                } for fb in p.feedback_options]  # Sorted by fb.id
            }

            # add the problem score to the total
            data[0]['max_score'] += problem_data['max_score']

            # return all solutions with the respective student id
            # for the corresponding problem that have been graded
            results = db.session.query(Solution, Submission.student_id)\
                                .join(Submission)\
                                .filter(Solution.problem_id == p.id,
                                        Solution.graded_by != None,
                                        Submission.student_id != None)\
                                .all() # noqa E711

            scores = defaultdict(int)
            sols_by_student = defaultdict(int)
            for sol, student_id in results:
                mark = (sum(list(fo.score for fo in sol.feedback)) if sol.feedback else nan)

                scores[student_id] += mark
                data[0]['scores'][student_id] += mark

                if not isnan(mark):
                    # do not count blank solutions
                    sols_by_student[student_id] += 1

            # count how many extra solutions where needed to solve this problem as
            # the total graded and non blank solutions minus the number of students
            # with at least one solution
            problem_data['extra_solutions'] = sum(list(sols_by_student.values())) - len(sols_by_student)

            problem_data['scores'] = scores

            problem_data['graders'] = grader_data(p.id)

            data[p.id] = problem_data

        full_scores = pd.DataFrame({id: dict(problem_data['scores']) for id, problem_data in data.items()})
        for p in exam.problems:
            data[p.id]['scores'] = scores_to_data(data[p.id]['scores'])
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
        data[0]['alpha'] = alpha
        data[0]['scores'] = scores_to_data(data[0]['scores'])
        data[0]['extra_copies'] = (db.session.query(func.count(Submission.id))
                                   .filter(Submission.exam_id == exam.id, Submission.student_id != None) # noqa E711
                                   .scalar()) - students

        return {
            'id': exam.id,
            'name': exam.name,
            'students': students,
            'problems': [data[p.id] for p in exam.problems],
            'total': data[0]
        }
