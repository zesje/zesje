'''
Script to generate a complete database of mock data for testing.
For each exam it generates a pdf with 3 problems per page, where
the number of pages is specified in the arguments.

You can create the sample data by running `python example_data.py -h`:

Usage:
    example_data.py [-h] [-d] [--exams EXAMS] [--pages PAGES]
                       [--students STUDENTS] [--graders GRADERS]
                       [--grade {nothing,partial,all}]

    optional arguments:
      -h, --help            show this help message and exit
      -d, --delete          delete previous data, if specified it removes all previously existing data
      --exams EXAMS         number of exams to add, default to 1
      --pages PAGES         number of pages per exam, default to 3
      --students STUDENTS   number of students per exam, default to 60
      --graders GRADERS     number of graders, default to 4
      --solve {nothing,partial,all}
                            how much of the solutions to solve, default to all
      --grade {nothing,partial,all}
                            how much of the exam to grade, default to partial.
'''

import random
import os
import shutil
import sys
import argparse

import lorem
import names
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from pdfrw import PdfReader, PdfWriter, PageMerge
from tempfile import NamedTemporaryFile

from lorem.text import TextLorem

from zesje.database import db, Exam, Scan
from zesje.scans import _process_pdf
from zesje.factory import create_app

sys.path.append(os.getcwd())


if 'ZESJE_SETTINGS' not in os.environ:
    os.environ['ZESJE_SETTINGS'] = '../zesje.dev.cfg'


lorem_name = TextLorem(srange=(1, 3))


def init_app(delete):
    app = create_app()

    if os.path.exists(app.config['DATA_DIRECTORY']) and delete:
        shutil.rmtree(app.config['DATA_DIRECTORY'])

    # ensure directories exists
    os.makedirs(app.config['DATA_DIRECTORY'], exist_ok=True)
    os.makedirs(app.config['SCAN_DIRECTORY'], exist_ok=True)

    with app.app_context():
        if delete:
            db.drop_all()
        db.create_all()

    return app


def generate_exam_pdf(pdf_file, exam_name, pages, problems):
    pdf = canvas.Canvas(pdf_file.name, pagesize=A4)
    for i in range(pages):
        generate_exam_page(pdf, exam_name, page_num=i, problems=problems)
        pdf.showPage()
    pdf.save()


def generate_exam_page(pdf, exam_name, page_num, problems):
    pdf.drawString(250, 650, exam_name)
    for i in range(3):
        generate_problem(pdf, problems[3 * page_num + i])


def generate_problem(pdf, problem):
    margin = 5

    pdf.drawString(problem['x'], problem['y'], problem['question'])
    pdf.rect(problem['x'], problem['y'] - problem['h'] - margin, problem['w'], problem['h'])


def generate_students(students):
    return [{
        'studentID': str(i + 1000001),
        'firstName': names.get_first_name(),
        'lastName': names.get_last_name(),
        'email': str(i + 1000000) + '@fakestudent.tudelft.nl'
    } for i in range(students)]


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


def generate_solution(pdf, problems, solve_all):
    pages = len(problems) // 3

    for p in range(pages):
        pdf.setFillColorRGB(0, 0, 1)

        for i in range(3):
            prob = problems[3 * p + i]
            if solve_all or random.random() < 0.5:
                pdf.drawString(prob['x'] + 50, prob['y'] - 50, lorem.sentence())

        pdf.showPage()


def solve_problems(pdf_file, pages, students, problems, solve):
    if solve == 'nothing':
        return

    with NamedTemporaryFile() as sol_file:
        pdf = canvas.Canvas(sol_file.name, pagesize=A4)

        for s in range(students):
            generate_solution(pdf, problems, solve == 'all')

            if pages % 2 == 1:
                # for an odd number of pages, zesje adds a blank page at the end
                pdf.showPage()

        pdf.save()

        exam_pdf = PdfReader(pdf_file)
        overlay_pdf = PdfReader(sol_file)

        for page_idx, exam_page in enumerate(exam_pdf.pages):
            overlay_merge = PageMerge().add(overlay_pdf.pages[page_idx])[0]
            exam_merge = PageMerge(exam_page).add(overlay_merge)
            exam_merge.render()

        PdfWriter(pdf_file.name, trailer=exam_pdf).write()


def grade_problems(exam_id, graders, problems, submission_ids, grade):
    if grade == 'nothing':
        return

    student_ids = [s['id'] for s in client.get(f'/api/students').get_json()]

    for i in range(len(submission_ids)):
        submission_id = submission_ids[i]
        # assign a student to each submission
        client.put(f'/api/submissions/{exam_id}/{submission_id}', json={'studentID': student_ids.pop()})

        # Only grade half the problems for each submission if grading partially.
        # TODO: in patial mode, grade only those problems that are solved
        problems = random.sample(problems, (len(problems) // 2) + 1) if grade == 'partial' else problems

        for problem in problems:
            feedback_options = problem['feedback']
            option = feedback_options[random.randint(1, len(feedback_options) - 1)]
            client.put(f"/api/solution/{exam_id}/{submission_id}/{problem['id']}",
                       json={
                           'id': option['id'],
                           'graderID': random.choice(graders)['id']
                       })


def create_exam(pages, students, grade, solve):
    exam_name = lorem_name.sentence().replace('.', '')
    problems = [{
        'question': str(i + 1) + '. ' + lorem.sentence().replace('.', '?'),
        'num': i + 1,
        'x': 75, 'y': 550 - (170 * (i % 3)),
        'w': 450, 'h': 120
    } for i in range(pages * 3)]

    with NamedTemporaryFile() as pdf_file:
        generate_exam_pdf(pdf_file, exam_name, pages, problems)
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
            'page': (problem['num'] - 1) // 3,
            # add some padding to x, y, w, h
            'x': problem['x'] - 20,
            'y': problem['y'] + 60,
            'width': problem['w'] + 40,
            'height': problem['h'] + 60,
        }).get_json()['id']
        # Have to put name again, because the endpoint first guesses a name.
        client.put(f'api/problems/{problem_id}', data={'name': problem['question'], 'grading_policy': 'set_nothing'})

        for _ in range(random.randint(2, 6)):
            client.post('api/feedback/' + str(problem_id), data={
                'name': lorem_name.sentence(),
                'description': (lorem.sentence() if random.choice([True, False]) else ''),
                'score': random.randint(0, 10)
            })

    client.put(f'api/exams/{exam_id}', data={'finalized': True})

    print('\tGenerating PDFs.')
    # Generate PDFs
    client.post(f'api/exams/{exam_id}/generated_pdfs', data={"copies_start": 1, "copies_end": students})
    # Download PDFs
    generated = client.get(f'api/exams/{exam_id}/generated_pdfs',
                           data={"copies_start": 1, "copies_end": students, 'type': 'pdf'})

    # Upload submissions
    with NamedTemporaryFile(mode='w+b') as submission_pdf:
        submission_pdf.write(generated.data)
        submission_pdf.seek(0)

        print('\tSolving submissions.')
        solve_problems(submission_pdf, pages, students, problems, solve)
        submission_pdf.seek(0)
        print('\tProcessing submissions. This may take a while.')

        handle_pdf_processing(exam_id, submission_pdf)

    submission_ids = [sub['id'] for sub in client.get(f'api/submissions/{exam_id}').get_json()]
    problems = client.get('/api/exams/' + str(exam_id)).get_json()['problems']

    graders = client.get('/api/graders').get_json()

    print('\tGrading problems.')
    grade_problems(exam_id, graders, problems, submission_ids, grade)

    # exam_data = client.get('/api/exams/' + str(exam_id)).get_json()
    # print(exam_data)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Create example exam data in the database.')
    parser.add_argument('-d', '--delete', action='store_true', help='delete previous data')
    parser.add_argument('--exams', type=int, default=1, help='number of exams to add')
    parser.add_argument('--pages', type=int, default=3, help='number of pages per exam')
    parser.add_argument('--students', type=int, default=60, help='number of students per exam')
    parser.add_argument('--graders', type=int, default=4, help='number of graders')
    parser.add_argument('--grade', type=str, default='partial', choices=['nothing', 'partial', 'all'],
                        help='how much of the exam to grade.')
    parser.add_argument('--solve', type=str, default='all', choices=['nothing', 'partial', 'all'],
                        help='how much of the solutions to solve')

    args = parser.parse_args(sys.argv[1:])

    app = init_app(args.delete)

    with app.test_client() as client:
        # create students
        for student in generate_students(args.students):
            client.put('api/students', data=student)

        # create graders
        for _ in range(args.graders):
            client.post('/api/graders', data={'name': names.get_full_name()})

        for _ in range(args.exams):
            create_exam(args.pages, args.students, args.grade, args.solve)
