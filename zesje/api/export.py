from io import BytesIO

from flask import send_file, stream_with_context, Response, current_app
import zipstream
import json

from ._helpers import ApiError
from ..database import Exam, Submission
from ..statistics import full_exam_data, grader_data
from ..emails import solution_pdf
from ..mysql import dump


def full():
    """Export the complete database

    Returns
    -------
    response : flask Response
        response containing the ``course.sql``
    """

    try:
        output = dump(current_app.config)
    except Exception as e:
        raise ApiError('Could not export database content: ' + str(e), 500)

    return send_file(
        BytesIO(output),
        as_attachment=True,
        download_name='course.sql',
        mimetype="application/sql",
        max_age=0
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

    if file_format not in ('dataframe', 'xlsx', 'xlsx_detailed'):
        raise ApiError('File format is not one of [dataframe, xlsx, xlsx_detailed]', 422)

    try:
        data = full_exam_data(exam_id)
    except KeyError as e:
        raise ApiError(str(e), 404)

    serialized = ResilientBytesIO()

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
        download_name=f'exam{exam_id}.{extension}',
        mimetype=mimetype,
        max_age=0
    )


def zipped_exam_solutions_generator(exam_id, anonymous):
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
    z = zipstream.ZipFile(mode='w')

    subs = Submission.query.filter(Submission.exam_id == exam_id, Submission.validated).all()

    for sub in subs:
        student = sub.student

        if anonymous:
            copy_numbers = list(copy.number for copy in sub.copies)
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
        raise ApiError(f"Exam with id #{exam_id} does not exist.", 404)

    generator = zipped_exam_solutions_generator(exam_id, exam_data.grade_anonymous)
    response = Response(stream_with_context(generator), mimetype='application/zip')
    response.headers['Content-Disposition'] = f'attachment; filename=exam{exam_id}.zip'
    return response


def grader_statistics(exam_id):
    """Export grader data in a txt file.

    Parameters
    ----------
    exam_id : int

    Returns
    -------
    response : flask Response
        response containing grader statistics as JSON.
    """

    try:
        data = grader_data(exam_id)
        data_str = json.dumps(data)

        serialized = BytesIO()
        serialized.write(data_str.encode('utf-8'))
        serialized.seek(0)
    except Exception:
        raise ApiError('Failed to load grader data.', 400)

    return send_file(
        serialized,
        as_attachment=True,
        download_name=f'grader_statistics_exam_{exam_id}.json',
        mimetype='application/json',
        max_age=0
    )


class ResilientBytesIO(BytesIO):
    def close(self):
        pass  # Refuse to close to avoid pandas bug

    def really_close(self):
        super().close()
