import os
from io import BytesIO
from flask import abort, Response, current_app as app
from pony import orm

import pandas
import numpy as np

from ..models import Exam, Submission
from ..helpers.db_helper import full_exam_data

import matplotlib
matplotlib.use('agg')
import seaborn
from matplotlib import pyplot

@orm.db_session
def get(exam_id):
    """Plot exam summary statistics.

    Parameters
    ----------
    exam_id : int

    Returns
    -------
    Image (JPEG mimetype)
    """
    try:
        exam = Exam[exam_id]
    except KeyError:
        abort(404)

    scores = {problem.name: max(list(problem.feedback_options.score) + [0])
              for problem in exam.problems}
    scores['total'] = sum(scores.values())

    full_scores = full_exam_data(exam_id)
    # Full exam data has multilevel columns (includes detailed feedback), we
    # flatten them out first.
    problem_scores = full_scores.iloc[
        :, full_scores.columns.get_level_values(1) == 'total'
    ]
    problem_scores.columns = problem_scores.columns.get_level_values(0)
    # Exclude empty columns from statistics
    problem_scores = problem_scores.loc[:, ~(problem_scores == 0).all()]

    seaborn.set()
    seaborn.set_context("notebook", font_scale=1.5, rc={"lines.linewidth": 2.5})

    cm = matplotlib.cm.magma
    # define the bins and normalize
    bounds = np.linspace(0, 1, 21)
    norm = matplotlib.colors.BoundaryNorm(bounds, cm.N)


    maxes = pandas.DataFrame(problem_scores.max())
    maxes['max_rubric'] = maxes.index
    maxes = maxes.replace({'max_rubric': scores}).max(axis=1)

    corrs = {column: (problem_scores[column]
                      .astype(float)
                      .corr(problem_scores
                            .total
                            .subtract(problem_scores[column])
                            .astype(float)
                           ).round(2)
                     ) for column in problem_scores if column != 'total'}

    alpha = ((len(problem_scores) - 1) / (len(problem_scores) - 2)
             * (1 - problem_scores.var()[:-1].sum()
                / problem_scores.total.var())
            )

    vals = [
        problem_scores[i].value_counts(normalize=True).sort_index().cumsum()
        for i in problem_scores
    ]
    data = np.array(
        [
            (-i, upper-lower, lower, num/maxes.ix[i])
            for i, val in enumerate(vals)
            for num, upper, lower in zip(
                val.index, val.data, [0] + list(val.data[:-1])
            )
        ]
    ).T
    fig = pyplot.figure(figsize=(12, 9))
    ax = fig.add_subplot(1, 1, 1)
    ax.barh(
        data[0], data[1], 0.5, data[2], color=cm(norm(data[3])), align='center'
    )
    ax.set_yticks(np.arange(0, -len(problem_scores.columns), -1));
    ax.set_yticklabels(
        [f'{i} ($Rir={corrs[i]:.2f}$)' for i in problem_scores.columns[:-1]]
        + [f'total: ($\\alpha = {alpha:.2f}$)']
    )
    ax.set_xlabel('fraction of students')
    ax.set_xlim(-0.025, 1.025)
    sm = matplotlib.cm.ScalarMappable(cmap=cm, norm=norm)
    sm._A = []
    colorbar = fig.colorbar(sm)
    colorbar.set_ticks(np.linspace(0, 1, 11))
    colorbar.set_label('score percentage')

    pyplot.tight_layout()
    image = BytesIO()
    pyplot.savefig(image)

    return Response(image.getvalue(), 200, mimetype='image/jpeg')
