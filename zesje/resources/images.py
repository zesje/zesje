import os
from flask import abort, Response, current_app as app
from pony import orm

from ..helpers import yaml_helper, image_helper
from ..models import Exam, Submission, Solution, Problem


@orm.db_session
def get(exam_id, problem_id, submission_id):
    """get student signature for the given submission.

    Parameters
    ----------
    exam_id : int
    problem_id : int
    submission_id : int
        The copy number of the submission. This uniquely identifies
        the submission *within a given exam*.

    Returns
    -------
    Image (JPEG mimetype)
    """
    try:
        exam = Exam[exam_id]
        sub = Submission.get(exam=exam, copy_number=submission_id)
        name = Problem[problem_id].name
    except (KeyError, ValueError):
        abort(404)

    data_dir = app.config['DATA_DIRECTORY']
    yaml_abspath = os.path.join(data_dir, sub.exam.yaml_path)
    *_, widgets = yaml_helper.parse(yaml_helper.read(yaml_abspath))
    problem_metadata = widgets.loc[name]
    page = f'page{int(problem_metadata.page)}.'
    page_path = (
        sub.pages
        .select(lambda p: page in p.path)
        .first().path
    )
    image = image_helper.get_widget_image(
        page_path,
        problem_metadata
    )

    return Response(image, 200, mimetype='image/jpeg')
