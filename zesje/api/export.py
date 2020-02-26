from io import BytesIO

from flask import abort, send_file, Response, current_app
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
        current_app.config['DB_PATH'],
        as_attachment=True,
        mimetype="application/x-sqlite3",
        cache_timeout=0,
    )


def exam(file_format, exam_id):
    """Export exam data in a file format

    Parameters
    ----------
    file_format : string
        One of "dataframe", "xlsx", "xlsx_detailed", "pdf".
    exam_id : int

    Returns
    -------
    response : flask Response
        response containing exam in specified file format.
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

    data.index.name = 'Student ID'

    # move the student names to the first columns
    cols = data.columns
    cols_names = data.columns.get_level_values(0).isin(['First name', 'Last name'])
    cols = list(cols[cols_names]) + list(cols[~cols_names])
    data = data[cols]

    if file_format == 'xlsx':
        cols_total = data.columns.get_level_values(1) == 'total'
        cols_total[:2] = True  # include student names
        data = data.iloc[:, cols_total]
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


def zipped_exam_solutions_generator(exam_id, anonymous, current_app):
    """Generator for exam solutions as a zip of (anonymized) pdfs

    Should only load the student solutions one at a time to decrease memory load.

    Parameters
    ----------
    exam_id : int
    anonymous : bool
        whether the pdfs and filenames need to be anonymized.
    current_app : flask app
        the current flask app as obtained by ``flask.current_app._get_current_object()``.

    Returns
    -------
    response : generator
        generator that yields parts of the zip.
    """
    with current_app.app_context():
        z = zipstream.ZipFile(mode='w')

        subs = Submission.query.filter(Submission.exam_id == exam_id).all()
        students = set(sub.student for sub in subs if sub.student)

        for student in students:
            if anonymous:
                copy_numbers = sorted(sub.copy_number for sub in subs if sub.student == student)
                file_name = f'cop{"y" if len(copy_numbers) == 1 else "ies"}-' \
                            f'{"-".join(str(number) for number in copy_numbers)}.pdf'
            else:
                file_name = f'student-{student.id}.pdf'

            z.write_iter(file_name, solution_pdf(exam_id, student.id, anonymous))
            yield from z.flush()

        yield from z


def exam_pdf(exam_id):
    """Export exam solutions as a zip of (anonymized) pdfs

    Parameters
    ----------
    exam_id : int

    Returns
    -------
    response : flask Response
        response streaming a zip containing (anonymized) pdfs of all student solutions.
    """
    exam_data = Exam.query.get(exam_id)
    if exam_data is None:
        abort(404)

    generator = zipped_exam_solutions_generator(exam_id, exam_data.grade_anonymous, current_app._get_current_object())
    response = Response(generator, mimetype='application/zip')
    response.headers['Content-Disposition'] = f'attachment; filename=exam{exam_id}.zip'
    return response
