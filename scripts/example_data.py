import itertools
import math
import random
import os
import shutil
import sys
import argparse

import lorem
import names
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from tempfile import NamedTemporaryFile

from lorem.text import TextLorem

from zesje.database import db, Exam, Scan
from zesje.scans import _process_pdf

sys.path.append(os.getcwd())
import zesje  # noqa: E402

parser = argparse.ArgumentParser(description='Create example exam data in the database.')
parser.add_argument('--exams', type=int, default=1, help='number of exams to add')
parser.add_argument('--pages', type=int, default=3, help='number of pages per exam')
parser.add_argument('--students', type=int, default=60, help='number of students per exam')
parser.add_argument('--graders', type=int, default=4, help='number of graders')
parser.add_argument('--grade', type=str, default='partial', choices=['nothing', 'partial', 'all'],
                    help='how much of the exam to grade')

args = parser.parse_args(sys.argv[1:])

if 'ZESJE_SETTINGS' not in os.environ:
    os.environ['ZESJE_SETTINGS'] = '../zesje.dev.cfg'

app = zesje.factory.create_app()
app.register_blueprint(zesje.api.api_bp, url_prefix='/api')

app.config.update(
    SQLALCHEMY_DATABASE_URI='sqlite:///' + '../scripts/data-dev/course.sqlite',
    SQLALCHEMY_TRACK_MODIFICATIONS=False  # Suppress future deprecation warning
)
if os.path.exists(app.config['DATA_DIRECTORY']):
    shutil.rmtree(app.config['DATA_DIRECTORY'])
os.makedirs(app.config['DATA_DIRECTORY'], exist_ok=True)
os.makedirs(app.config['SCAN_DIRECTORY'], exist_ok=True)

db.init_app(app)

with app.app_context():
    db.drop_all()
    db.create_all()

lorem_name = TextLorem(srange=(1, 3))


def generate_exam_pdf(pdf_file, exam_name, problems):
    pdf = canvas.Canvas(pdf_file.name, pagesize=A4)
    for i in range(args.pages):
        generate_exam_page(pdf, exam_name, page_num=i, problems=problems)
        pdf.showPage()
    pdf.save()


def generate_exam_page(pdf, exam_name, page_num, problems):
    pdf.drawString(20, 20, exam_name)
    for i in range(3):
        problem_num = 3 * page_num + i
        generate_problem(pdf, problems[problem_num])


def generate_problem(pdf, problem):
    margin = 5

    pdf.drawString(problem['x'], problem['y'], str(problem['num']) + ": " + problem['question'])
    pdf.rect(problem['x'], problem['y'] - problem['h'] - margin, problem['w'], problem['h'])


def generate_students():
    return [{
        'studentID': str(i + 1000001),
        'firstName': names.get_first_name(),
        'lastName': names.get_last_name(),
        'email': str(i + 1000000) + '@student.tudelft.nl'
    } for i in range(args.students)]


def handle_pdf_processing(exam_id, pdf):
    exam = Exam.query.get(exam_id)
    scan = Scan(exam=exam, name=pdf.name,
                status='processing', message='Waiting...')

    db.session.add(scan)
    db.session.commit()

    path = os.path.join(app.config['SCAN_DIRECTORY'], f'{scan.id}.pdf')
    with open(path, 'wb') as outfile:
        outfile.write(pdf.read())
        pdf.seek(0)

    _process_pdf(scan_id=scan.id, app_config=app.config)

    return {
        'id': scan.id,
        'name': scan.name,
        'status': scan.status,
        'message': scan.message
    }


def grade_problems(exam_id, graders, problems, submission_ids):
    if args.grade == 'nothing':
        return

    for submission_id in submission_ids:
        # Only grade half the problems for each submission if grading partially.
        problems = random.sample(problems, math.ceil(len(problems)/2)) if args.grade == 'all' else problems
        for problem in problems:
            # Exclude the 'blank' option
            feedback_options = problem['feedback'][1:]
            n_options_to_click = random.randint(1, len(feedback_options))
            options_to_click = [opt['id'] for opt in random.sample(feedback_options, n_options_to_click)]
            for option in options_to_click:
                client.put(f"/api/solution/{exam_id}/{submission_id}/{problem['id']}",
                           json={
                               'id': option,
                               'graderID': random.choice(graders)['id']
                           })

def create_exam():
    exam_name = lorem_name.sentence().replace('.', '')
    problems = [{
        'question': lorem.sentence().replace('.', '?'),
        'num': i + 1,
        'x': 75, 'y': 600 - (170 * (i % 3)),
        'w': 450, 'h': 120
    } for i in range(args.pages * 3)]
    with NamedTemporaryFile() as pdf_file:
        generate_exam_pdf(pdf_file, exam_name, problems)
        exam_id = client.post('/api/exams',
                              content_type='multipart/form-data',
                              data={
                                  'exam_name': exam_name,
                                  'pdf': pdf_file}).get_json()['id']

    # Create problems
    for problem in problems:
        problem_id = client.post('api/problems', data={
            'exam_id': exam_id,
            'name': problem['question'],
            'page': math.floor((problem['num'] - 1) / 3),
            # add some padding to x, y, w, h
            'x': problem['x'] - 20,
            'y': problem['y'] - 30,
            'width': problem['w'] + 40,
            'height': problem['h'] + 60,
        }).get_json()['id']
        # Have to put name again, because the endpoint first guesses a name.
        client.put('api/problems/' + str(problem_id),
                   data={'name': problem['question'], 'grading_policy': 'set_nothing'})
        for _ in range(random.randint(2, 6)):
            client.post('api/feedback/' + str(problem_id), data={
                'name': lorem_name.sentence(),
                'description': (lorem.sentence() if random.choice([True, False]) else ''),
                'score': random.randint(-4, 4)
            })

    client.put('api/exams/' + str(exam_id), data={
        'finalized': True
    })
    # create graders
    graders = None
    for _ in range(args.graders):
        graders = client.post('/api/graders', data={'name': names.get_full_name()}).get_json()

    # Generate PDFs
    client.post(f'api/exams/{exam_id}/generated_pdfs', data={"copies_start": 1, "copies_end": args.students})
    # Download PDFs
    generated = client.get(f'api/exams/{exam_id}/generated_pdfs',
                           data={"copies_start": 1, "copies_end": args.students, 'type': 'pdf'})

    # Upload submissions
    with NamedTemporaryFile(mode='w+b') as submission_pdf:
        submission_pdf.write(generated.data)
        submission_pdf.seek(0)
        print('Processing PDFs. This may take a while.')
        handle_pdf_processing(exam_id, submission_pdf)

    submission_ids = [sub['id'] for sub in client.get(f'api/submissions/{exam_id}').get_json()]
    problems = client.get('/api/exams/' + str(exam_id)).get_json()['problems']

    grade_problems(exam_id, graders, problems, submission_ids)

    exam_data = client.get('/api/exams/' + str(exam_id)).get_json()
    print(exam_data)


with app.test_client() as client:
    for student in generate_students():
        client.put('api/students', data=student).get_json()

    for _ in range(args.exams):
        create_exam()
