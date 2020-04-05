from math import isnan
from flask_restful import Resource

from ..database import Exam
from ..statistics import full_exam_data, grader_data


class Statistics(Resource):
    """Getting a list of uploaded scans, and uploading new ones."""

    def get(self, exam_id):
        """get all uploaded scans for a particular exam.

        Parameters
        ----------
        exam_id : int

        Returns
        -------
        list of:
            name: str
                filename of the uploaded PDF
        """

        exam = Exam.query.get(exam_id)
        if exam is None:
            return dict(status=404, message='Exam does not exist.'), 404

        max_scores = {problem.name: max(list(fb.score for fb in problem.feedback_options) + [0])
                      for problem in exam.problems}

        full_scores = full_exam_data(exam_id)
        # Full exam data has multilevel columns (includes detailed feedback), we
        # flatten them out first.
        problem_scores = full_scores.iloc[
            :, full_scores.columns.get_level_values(1) == 'total'
        ]
        problem_scores.columns = problem_scores.columns.get_level_values(0)

        corrs = {column: (problem_scores[column]  # noqa: E127
                          .astype(float)
                          .corr(problem_scores
                                .total
                                .subtract(problem_scores[column])
                                .astype(float)
                               )
                         ) for column in problem_scores if column != 'total'}

        if len(problem_scores) > 2 and problem_scores.total.var():
            alpha = ((len(problem_scores) - 1) / (len(problem_scores) - 2)
                     * (1 - problem_scores.var()[:-1].sum()
                        / problem_scores.total.var()))
        else:
            alpha = ''

        grader_stats = grader_data(exam.id)
        problem_graders = {p['name']: p['graders'] for p in grader_stats['problems']}

        feedbacks = {problem.name: [
            {
                'id': fb.id,
                'name': fb.text,
                'description': fb.description,
                'score': fb.score,
                'used': len(fb.solutions)
            }
            for fb in problem.feedback_options  # Sorted by fb.id
        ] for problem in exam.problems}

        return {
            'name': exam.name,
            'students': len(problem_scores),
            'problems': [
                {
                    'name': column,
                    'max_score': max_scores[column],
                    'scores': problem_scores[column].dropna().tolist(),
                    'correlation': corrs[column] if not isnan(corrs[column]) else '',
                    'graders': problem_graders[column],
                    'feedback': feedbacks[column]
                } for column in problem_scores if column != 'total'],
            'total': {
                'max_score': sum(max_scores.values()),
                'scores': problem_scores['total'].dropna().tolist(),
                'alpha': alpha
            }
        }
