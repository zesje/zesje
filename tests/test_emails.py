import pytest
import os

from pikepdf import Pdf
import numpy as np

from zesje.database import db, Exam, ExamLayout, ExamWidget, Submission, Copy, Page, Student
from zesje.emails import solution_pdf
from zesje.image_extraction import extract_image_pikepdf
from zesje.images import get_box
from zesje.scans import exam_student_id_widget


@pytest.mark.parametrize('layout, anonymous', [
    (ExamLayout.templated, False),
    (ExamLayout.templated, True),
    (ExamLayout.unstructured, False),
    (ExamLayout.unstructured, True)
], ids=['Templated', 'Templated & anonymous', 'Unstructured', 'Unstructured & anonymous'])
def test_solution_pdf(app, datadir, layout, anonymous):
    exam = Exam(name='Email', layout=layout, finalized=True)
    student = Student(id=1234323, first_name='Jamy', last_name='Macgiver', email='J.M@tudelft.nl')
    db.session.add(exam)
    db.session.add(student)
    db.session.commit()

    if layout == ExamLayout.templated:
        db.session.add(ExamWidget(
            name='student_id_widget',
            x=50,
            y=50,
            exam=exam,
        ))
        db.session.commit()

    sub = Submission(exam=exam, student=student, validated=True)
    db.session.add(sub)

    copy = Copy(submission=sub, number=1)
    db.session.add(copy)

    for index, filepath in enumerate(['studentnumbers/1234323.jpg', 'studentnumbers/4300947.jpg']):
        page = Page(number=index, path=os.path.join(datadir, filepath))
        db.session.add(page)
        copy.pages.append(page)
    db.session.commit()

    with Pdf.open(solution_pdf(exam.id, student.id, anonymous=anonymous)) as pdf:
        pagecount = len(pdf.pages)
        assert pagecount == 2

        if anonymous and layout == ExamLayout.templated:
            image = extract_image_pikepdf(pdf.pages[0])
            _, coords = exam_student_id_widget(exam.id)
            widget_area = get_box(np.array(image), np.array(coords, dtype=float) / 72, padding=-.3)
            w, h, *_ = widget_area.shape

            assert 145 < (np.mean(widget_area[:w//2]) + np.mean(widget_area[:, :h//2])) / 2 < 155
