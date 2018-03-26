import os
from io import BytesIO
from flask import abort, Response, current_app as app
from pony import orm

from ..helpers import db_helper


def full():
    """Export the complete database

    Returns
    -------
    course.sqlite
    """
    data_dir = app.config['DATA_DIRECTORY']

    with open(os.path.join(data_dir, 'course.sqlite'), 'rb') as f:
        data = f.read()
    resp = Response(data, 200)
    resp.headers.set('Content-Disposition', 'attachment',
                     filename='course.sqlite')
    return resp


def dataframe(exam_id):
    """Export exam data as a pandas dataframe

    Parameters
    ----------
    exam_id : int

    Returns
    -------
    exam.pd : pickled pandas dataframe
    """
    try:
        data = db_helper.full_exam_data(exam_id)
    except KeyError:
        abort(404)
    serialized = BytesIO()
    data.to_pickle(serialized)
    resp = Response(serialized.getvalue(), 200)
    resp.headers.set('Content-Disposition', 'attachment',
                     filename='exam.pd')
    return resp
