from io import BytesIO

from flask import abort, Response

from pony import orm

import matplotlib
import numpy as np
import pandas

from ..statistics import full_exam_data
from ..database import Exam

matplotlib.use('agg')
import seaborn  # noqa: E402
from matplotlib import pyplot  # noqa: E402


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

    seaborn.set()
    seaborn.set_context("paper", font_scale=1.5, rc={"lines.linewidth": 2.5})

    cm = matplotlib.cm.magma
    # define the bins and normalize
    bounds = np.linspace(0, 1, 21)
    norm = matplotlib.colors.BoundaryNorm(bounds, cm.N)

    maxes = pandas.DataFrame(problem_scores.max())
    maxes['max_rubric'] = maxes.index
    maxes = maxes.replace({'max_rubric': scores}).max(axis=1)

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
        alpha = np.nan

    vals = [
        problem_scores[i].value_counts().sort_index().cumsum()
        for i in problem_scores
    ]
    n_students = len(problem_scores)
    # Information about rectangles to draw.
    data = np.array(
        [
            (-i, (upper-lower)/n_students, lower/n_students, num/maxes.ix[i])
            for i, val in enumerate(vals)
            for num, upper, lower in zip(
                val.index, list(val), [0] + list(val[:-1])
            )
        ]
    ).T
    fig = pyplot.figure(figsize=(12, 9))
    ax = fig.add_subplot(1, 1, 1)

    # Draw actual percentages
    ax.barh(
        data[0], data[1], 0.5, data[2], color=cm(norm(data[3])), align='center'
    )

    # Draw bars for each problem
    ax.barh(
        -np.arange(len(vals)), 1, 0.5, 0, align='center',
        linestyle='solid', linewidth=1, edgecolor=(0, 0, 0, .5),
        facecolor=(0, 0, 0, 0),
    )
    ax.set_yticks(np.arange(0, -len(problem_scores.columns), -1))
    ax.set_yticklabels(
        [(f'{i} ' + f'($Rir={corrs[i]:.2f}$)' * (not np.isnan(corrs[i]))) for i
         in problem_scores.columns[:-1]]
        + ['total ' + f'($\\alpha = {alpha:.2f}$)' * (not np.isnan(alpha))]
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
    pyplot.show()

    return Response(image.getvalue(), 200, mimetype='image/jpeg')
