from io import BytesIO

from flask import abort, send_file, current_app as app
import cv2
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

from ..database import db, Exam, Submission, Student
from ..images import get_box, guess_dpi, widget_area
from .images import _grey_out_student_widget
from ..statistics import full_exam_data
from ..scans import exam_student_id_widget
from ..api.exams import PAGE_FORMATS


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


def exam_pdf(exam_id):
    exam_data = Exam.query.get(exam_id)
    if exam_data is None:
        abort(404)

    pages = sorted((p for sub in exam_data.submissions for p in sub.pages), key=lambda p: (p.submission.id, p.number))

    page_format = app.config.get('PAGE_FORMAT', 'A4')  # TODO Remove default value
    page_size = PAGE_FORMATS[page_format]

    serialized = BytesIO()
    pdf = canvas.Canvas(serialized, pagesize=page_size)

    for page in pages:
        page_path = page.path

        page_im = cv2.imread(page_path)

        dpi = guess_dpi(page_im)

        if exam_data.grade_anonymous and page.number == 0:
            student_id_widget, coords = exam_student_id_widget(exam_id)
            # coords are [ymin, ymax, xmin, xmax]
            page_im = _grey_out_student_widget(page_im, coords, dpi)

        # convert cv2 image to pil image
        page_im = cv2.cvtColor(page_im, cv2.COLOR_BGR2RGB)
        pil_im = Image.fromarray(page_im)

        # convert pil image to pdf
        pdf.drawImage(ImageReader(pil_im), 0, 0, width=page_size[0], height=page_size[1])
        pdf.showPage()

    pdf.save()
    serialized.seek(0)

    return send_file(
        serialized,
        as_attachment=True,
        attachment_filename=f'exam{exam_id}.pdf',
        mimetype='application/pdf',
        cache_timeout=0,
    )
