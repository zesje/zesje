import os
from io import BytesIO

from flask import abort, Response, current_app as app

from ..statistics import full_exam_data


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


def exam(file_format, exam_id):
    """Export exam data as a pandas dataframe

    Parameters
    ----------
    file_format : string
        One of "dataframe", "xlsx", "xlsx_detailed"
    exam_id : int

    Returns
    -------
    exam.pd : pickled pandas dataframe
    """
    try:
        data = full_exam_data(exam_id)
    except KeyError:
        abort(404)
    serialized = BytesIO()
    extension = "pd" if file_format == 'dataframe' else "xlsx"
    if file_format == 'dataframe':
        data.to_pickle(serialized)
    elif file_format == 'xlsx':
        data = data.iloc[:, data.columns.get_level_values(1) == 'total']
        data.columns = data.columns.get_level_values(0)
        data.to_excel(serialized)
    elif file_format == 'xlsx_detailed':
        data.to_excel(serialized)
    else:
        abort(404)
    resp = Response(serialized.getvalue(), 200)
    resp.headers.set('Content-Disposition', 'attachment',
                     filename=f'exam{exam_id}.{extension}')
    return resp
