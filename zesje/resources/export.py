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
