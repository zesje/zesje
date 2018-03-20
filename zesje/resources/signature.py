import os
from flask import abort, Response, current_app as app
from pony import orm

from ..helpers import yaml_helper, image_helper
from ..models import Exam, Submission


@orm.db_session
def get(exam_id, submission_id):
    """get student signature for the given submission.

    Parameters
    ----------
    exam_id : int
    submission_id : int
        The copy number of the submission. This uniquely identifies
        the submission *within a given exam*.

    Returns
    -------
    Image (JPEG mimetype)
    """
    # We could register an app-global error handler for this,
    # but it would add more code then it removes.
    exam = Exam.get(id=exam_id)
    if not exam:
        abort(404)
    sub = Submission.get(exam=exam, copy_number=submission_id)
    if not sub:
        abort(404)

    data_dir = app.config['DATA_DIRECTORY']
    yaml_abspath = os.path.join(data_dir, sub.exam.yaml_path)
    *_, widgets = yaml_helper.parse(yaml_helper.read(yaml_abspath))
    first_page = next(p.path for p in sub.pages if 'page1.jpg' in p.path)
    image = image_helper.get_widget_image(first_page,
                                          widgets.loc['studentnr'])

    return Response(image, 200, mimetype='image/jpeg')
