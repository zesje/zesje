from io import BytesIO

from flask import abort, send_file, Response, current_app as app
import zipstream

from ..database import Exam, Submission
from ..statistics import full_exam_data
from ..emails import solution_pdf


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
        One of "dataframe", "xlsx", "xlsx_detailed", "pdf"
    exam_id : int

    Returns
    -------
    exam.pd : pickled pandas dataframe
    """
    if file_format == 'pdf':
        return exam_pdf(exam_id)

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


def _generator(exam_id, anonymous, current_app):
    with current_app.app_context():
        z = zipstream.ZipFile(mode='w')

        subs = Submission.query.filter(Submission.exam_id == exam_id)
        student_ids = sorted(set(sub.student.id for sub in subs))

        for counter, student_id in enumerate(student_ids):
            z.write_iter(f'student{counter}.pdf', solution_pdf(exam_id, student_id, anonymous))
            yield from z.flush()

        yield from z


def exam_pdf(exam_id):
    exam_data = Exam.query.get(exam_id)
    if exam_data is None:
        abort(404)

    response = Response(_generator(exam_id, exam_data.grade_anonymous, app._get_current_object()), mimetype='application/zip')
    response.headers['Content-Disposition'] = 'attachment; filename={}'.format('files.zip')
    return response
