import os
import sys
import argparse

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from tempfile import NamedTemporaryFile

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

for _ in range(args.exams):

    with NamedTemporaryFile() as pdf_file:
        canvas = canvas.Canvas(pdf_file.name, pagesize=A4)
        for _ in range(args.pages - 1):
            canvas.showPage()
        canvas.save()
