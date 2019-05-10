from io import BytesIO

from flask import abort, send_file, current_app as app

from ..statistics import full_exam_data


def full():
    """Export the complete database

    Returns
    -------
    response : flask Response
        response containing the ``course.sqlite``
    """
    return send_file(
        app.config['DB_PATH'],
        as_attachment=True,
        mimetype="application/x-sqlite3",
        cache_timeout=0,
    )


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

    if file_format not in ('dataframe', 'xlsx', 'xlsx_detailed'):
        abort(404)

    serialized = BytesIO()

    if file_format == 'xlsx':
        data = data.iloc[:, data.columns.get_level_values(1) == 'total']
        data.columns = data.columns.get_level_values(0)

    if file_format == 'dataframe':
        extension = 'pd'
        mimetype = 'application/python-pickle'
        data.to_pickle(serialized, compression=None)
    else:
        extension = 'xlsx'
        mimetype = (
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        data.to_excel(serialized)

    serialized.seek(0)

    return send_file(
        serialized,
        as_attachment=True,
        attachment_filename=f'exam{exam_id}.{extension}',
        mimetype=mimetype,
        cache_timeout=0,
    )
