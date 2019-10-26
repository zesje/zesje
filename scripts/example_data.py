import os
import sys
import argparse

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from tempfile import NamedTemporaryFile

import lorem

sys.path.append(os.getcwd())
import zesje  # noqa: E402

parser = argparse.ArgumentParser(description='Create example exam data in the database.')
parser.add_argument('--exams', type=int, default=1, help='number of exams to add')
parser.add_argument('--pages', type=int, default=3, help='number of pages per exam')
parser.add_argument('--students', type=int, default=60, help='number of students per exam')

args = parser.parse_args(sys.argv[1:])

if 'ZESJE_SETTINGS' not in os.environ:
    os.environ['ZESJE_SETTINGS'] = '../zesje.dev.cfg'

app = zesje.factory.create_app()
app.register_blueprint(zesje.api.api_bp, url_prefix='/api')

client = app.test_client()


def generate_exam_page(pdf, page_num):
    for problem_num in range(3):
        generate_problem(pdf, 75, 600 - (170 * problem_num), 3 * page_num + problem_num + 1)
    pdf.showPage()


def generate_problem(pdf, x, y, problem_num):
    margin = 5
    box_size = {'w': 450, 'h': 100}
    question = lorem.sentence().replace('.', '?')
    pdf.drawString(x, y, f'{problem_num}: {question}')
    pdf.rect(x, y - box_size['h'] - margin, box_size['w'], box_size['h'])


def generate_exam_pdf():
    with NamedTemporaryFile() as pdf_file:
        pdf = canvas.Canvas(pdf_file.name, pagesize=A4)
        for i in range(args.pages):
            generate_exam_page(pdf, page_num=i)
        pdf.save()


for _ in range(args.exams):
    generate_exam_pdf()


