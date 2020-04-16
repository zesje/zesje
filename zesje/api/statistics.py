from math import isnan, nan
from flask_restful import Resource
from collections import defaultdict
import pandas as pd
from sqlalchemy import func

from ..database import db, Exam, Submission, Solution, Grader
from ..statistics import estimate_grading_time


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

        students = db.session.query(func.count(Submission.student_id))\
            .filter(Submission.exam_id == exam.id, Submission.student_id != None)\
            .scalar() # noqa E711

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

            # query that resunts a map (solution, student_id)
            # filtered by problem_id and graded
            results = db.session.query(Solution, Submission.student_id)\
                                .join(Submission)\
                                .filter(Solution.problem_id == p.id, Solution.graded_by != None)\
                                .all() # noqa E711

            scores = defaultdict(int)
            graders = defaultdict(int)
            sols_by_student = defaultdict(int)
            for sol, student_id in results:
                mark = (sum(list(fo.score for fo in sol.feedback)) if sol.feedback else nan)

                scores[student_id] += mark
                data[0]['scores'][student_id] += mark

                if not isnan(mark):
                    # do not count blank solutions
                    sols_by_student[student_id] += 1

                graders[sol.grader_id] += 1

            # query that counts the number of sol per student and problem id:
            # SELECT submission.student_id, count(submission.student_id)
            # FROM submission INNER JOIN solution
            # ON solution.submission_id == submission.id AND solution.problem_id == 2
            # GROUP BY submission.student_id;
            problem_data['extra_solutions'] = sum(list(sols_by_student.values())) - len(sols_by_student)

            problem_data['scores'] = scores

            problem_data['graders'] = []

            for grader_id, graded in graders.items():
                grader = Grader.query.get(grader_id)
                avg, total = estimate_grading_time(p.id, grader_id)

                problem_data['graders'].append({
                    'id': grader.id,
                    'name': grader.name,
                    'graded': graded,
                    'avg_grading_time': avg,
                    'total_grading_time': total
                })

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
                                   .filter(Submission.exam_id == exam.id)
                                   .scalar()) - students

        return {
            'id': exam.id,
            'name': exam.name,
            'students': students,
            'problems': [data[p.id] for p in exam.problems],
            'total': data[0]
        }
