#!/usr/bin/env python3

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
      -h, --help           show this help message and exit
      -d, --delete         delete previous data
      --exams (int)        number of exams to add
      --pages (int)        number of pages per exam
      --students (int)     number of students per exam
      --graders (int)      number of graders
      --solve (float)      how much of the solutions to solve (between 0 and 100)
      --grade (float)      how much of the exam to grade (between 0 and 100). Notice that only non-
                           blank solutions will be considered for grading.

'''

import random
import os
import shutil
import sys
import argparse

import lorem
import names
import flask_migrate
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from pdfrw import PdfReader, PdfWriter, PageMerge
from tempfile import NamedTemporaryFile

from lorem.text import TextLorem

from zesje.database import db, Exam, Scan, Submission, Solution, Page
from zesje.scans import _process_pdf
from zesje.factory import create_app


if 'ZESJE_SETTINGS' not in os.environ:
    os.environ['ZESJE_SETTINGS'] = '../zesje_dev_cfg.py'


lorem_name = TextLorem(srange=(1, 3))
lorem_prob = TextLorem(srange=(2, 5))


def init_app(delete):
    app = create_app()

    if os.path.exists(app.config['DATA_DIRECTORY']) and delete:
        shutil.rmtree(app.config['DATA_DIRECTORY'])

    # ensure directories exists
    os.makedirs(app.config['DATA_DIRECTORY'], exist_ok=True)
    os.makedirs(app.config['SCAN_DIRECTORY'], exist_ok=True)

    # Only create the database from migrations if it was deleted.
    # Otherwise the user should migrate manually.
    if delete:
        with app.app_context():
            flask_migrate.upgrade(directory='migrations')

    return app


def generate_exam_pdf(pdf_file, exam_name, pages, problems, mc_problems):
    pdf = canvas.Canvas(pdf_file.name, pagesize=A4)

    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(A4[0] / 2 - 100, 650, exam_name)
    pdf.setFont("Helvetica", 11.5)

    for i in range(pages):
        generate_exam_page(pdf, exam_name, page_num=i, problems=problems, mc_problems=mc_problems)
        pdf.showPage()
    pdf.save()


def generate_exam_page(pdf, exam_name, page_num, problems, mc_problems):
    if page_num > 0:
        generate_problem(pdf, mc_problems[page_num - 1])

    for i in range(3):
        generate_problem(pdf, problems[3 * page_num + i])


def generate_problem(pdf, problem):
    margin = 5

    pdf.drawString(problem['x'], problem['y'], problem['question'])
    pdf.rect(problem['x'], problem['y'] - problem['h'] - margin, problem['w'], problem['h'])


def generate_students(students):
    return [{
        'studentID': str(i + 1000000),
        'firstName': names.get_first_name(),
        'lastName': names.get_last_name(),
        'email': str(i + 1000000) + '@fakestudent.tudelft.nl'
    } for i in range(students)]


def _fake_process_pdf(scan, pages, student_ids):
    for copy in range(1, len(student_ids) + 1):
        sub = Submission(copy_number=copy, exam=scan.exam, student_id=student_ids[copy - 1])
        db.session.add(sub)

        for problem in scan.exam.problems:
            db.session.add(Solution(problem=problem, submission=sub))

        base_copy_path = os.path.join(f'{scan.exam.id}_data', 'submissions', f'{copy}')
        for page in range(pages + 1):
            db.session.add(Page(path=os.path.join(base_copy_path, f'page{page:02d}.jpg'), submission=sub, number=page))

    scan.status = 'success'
    db.session.commit()


def handle_pdf_processing(app, exam_id, pdf, pages, student_ids, skip_processing=False):
    exam = Exam.query.get(exam_id)
    scan = Scan(exam=exam, name=pdf.name,
                status='processing', message='Waiting...')

    db.session.add(scan)
    db.session.commit()

    path = os.path.join(app.config['SCAN_DIRECTORY'], f'{scan.id}.pdf')
    with open(path, 'wb') as outfile:
        outfile.write(pdf.read())
        pdf.seek(0)

    if skip_processing:
        _fake_process_pdf(scan, pages, student_ids)
    else:
        _process_pdf(scan_id=scan.id)

    return {
        'id': scan.id,
        'name': scan.name,
        'status': scan.status,
        'message': scan.message
    }


def generate_solution(pdf, student_id, problems, mc_problems, solve):
    pages = len(problems) // 3

    pdf.setFillColorRGB(0, 0.5, 1)

    sID = str(student_id)
    for k in range(7):
        d = int(sID[k])
        pdf.rect(68 + k * 16, int(A4[1]) - 80 - d * 16, 5, 5, fill=1, stroke=0)

    for p in range(pages):
        pdf.setFillColorRGB(0, 0.5, 1)

        if p > 0 and random.random() < solve:
            o = random.choice(mc_problems[p - 1]['mc_options'])
            pdf.rect(o['x'] + 2, o['y'] + 4, 5, 5, fill=1, stroke=0)

        for i in range(3):
            prob = problems[3 * p + i]
            if random.random() < solve:
                pdf.drawString(prob['x'] + 50, prob['y'] - 50, lorem.sentence())

        pdf.showPage()


def solve_problems(pdf_file, pages, student_ids, problems, mc_problems, solve):
    if solve < 0.01:
        # nothing to solve
        return

    with NamedTemporaryFile() as sol_file:
        pdf = canvas.Canvas(sol_file.name, pagesize=A4)

        for id in student_ids:
            generate_solution(pdf, id, problems, mc_problems, solve)

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


def grade_problems(client, exam_id, graders, problems, submissions, grade):
    for k in range(len(submissions)):
        sub = submissions[k]
        submission_id = sub['id']

        for prob in sub['problems']:
            # randomly select the problem if it is not blanck
            if random.random() <= grade and len(prob['feedback']) == 0:
                fo = next(filter(lambda p: p['id'] == prob['id'], problems))['feedback']
                opt = fo[random.randint(0, len(fo) - 1)]
                client.put(f"/api/solution/{exam_id}/{submission_id}/{prob['id']}",
                           json={
                               'id': opt['id'],
                               'graderID': random.choice(graders)['id']
                           })


def design_exam(app, client, pages, students, grade, solve, skip_processing):
    exam_name = lorem_name.sentence().replace('.', '')
    problems = [{
        'question': str(i + 1) + '. ' + lorem_prob.sentence().replace('.', '?'),
        'page': (i // 3),
        'x': 75, 'y': int(A4[1]) - 300 - (170 * (i % 3)),
        'w': 450, 'h': 120
    } for i in range(pages * 3)]

    mc_problems = [{
        'question': f'MC{i}. ' + lorem_prob.sentence().replace('.', '?'),
        'x': 75, 'y': int(A4[1]) - 150,
        'w': 300, 'h': 75,
        'page': i,
        'mc_options': []
    } for i in range(1, pages)]

    with NamedTemporaryFile() as pdf_file:
        generate_exam_pdf(pdf_file, exam_name, pages, problems, mc_problems)
        exam_id = client.post('/api/exams',
                              content_type='multipart/form-data',
                              data={
                                  'exam_name': exam_name,
                                  'pdf': pdf_file}).get_json()['id']

    print('\tDesigning a hard exam.')
    # Create problems
    for problem in problems:
        problem_id = client.post('api/problems', data={
            'exam_id': exam_id,
            'name': problem['question'],
            'page': problem['page'],
            # add some padding to x, y, w, h
            'x': problem['x'] - 20,
            'y': problem['y'] + 60,
            'width': problem['w'] + 40,
            'height': problem['h'] + 60,
        }).get_json()['id']
        # Have to put name again, because the endpoint first guesses a name.
        client.put(f'api/problems/{problem_id}', data={'name': problem['question'], 'grading_policy': 'set_blank'})

        for _ in range(random.randint(2, 10)):
            client.post(f'api/feedback/{problem_id}', data={
                'name': lorem_name.sentence(),
                'description': (lorem.sentence() if random.choice([True, False]) else ''),
                'score': random.randint(0, 10)
            })

    for problem in mc_problems:
        problem_id = client.post('api/problems', data={
            'exam_id': exam_id,
            'name': problem['question'],
            'page': problem['page'],
            # add some padding to x, y, w, h
            'x': problem['x'] - 20,
            'y': int(A4[1]) - problem['y'] - 20,
            'width': problem['w'] + 40,
            'height': problem['h'] + 40,
        }).get_json()['id']
        # Have to put name again, because the endpoint first guesses a name.
        client.put(f'api/problems/{problem_id}', data={'name': problem['question'], 'grading_policy': 'set_single'})

        fops = []
        for k in range(random.randint(2, 5)):
            label = chr(65 + k)
            x = problem['x'] + 20 * (k + 1)
            problem['mc_options'].append({'name': label, 'x': x, 'y': problem['y'] - 50})
            resp = client.put('api/mult-choice/', data={
                'problem_id': problem_id,
                'name': label, 'label': label,
                'x': x,
                'y': int(A4[1]) - problem['y'] + 40
            })
            fops.append((resp.get_json()['feedback_id'], chr(k + 65)))

        correct = random.choice(fops)
        client.put(f'api/feedback/{problem_id}', data={'id': correct[0], 'name': correct[1], 'score': 1})

    client.put(f'api/exams/{exam_id}', data={'finalized': True})

    # Download PDFs
    generated = client.get(f'api/exams/{exam_id}/generated_pdfs',
                           data={"copies_start": 1, "copies_end": students, 'type': 'pdf'})

    student_ids = [s['id'] for s in client.get(f'/api/students').get_json()]
    random.shuffle(student_ids)
    student_ids = student_ids[:students]

    # Upload submissions
    with NamedTemporaryFile(mode='w+b') as submission_pdf:
        submission_pdf.write(generated.data)
        submission_pdf.seek(0)

        print('\tWaiting for students to solve it.')
        solve_problems(submission_pdf, pages, student_ids, problems, mc_problems, solve)
        submission_pdf.seek(0)

        print('\tProcessing scans (this may take a while).',)
        handle_pdf_processing(app, exam_id, submission_pdf, pages, student_ids, skip_processing)

    submissions = client.get(f'api/submissions/{exam_id}').get_json()
    problems = client.get('/api/exams/' + str(exam_id)).get_json()['problems']

    graders = client.get('/api/graders').get_json()

    print('\tIt\'s grading time.')
    grade_problems(client, exam_id, graders, problems, submissions, grade)

    print('\tAll done!')
    return client.get('/api/exams/' + str(exam_id)).get_json()


def create_exams(app, client, exams, pages, students, graders, solve, grade, skip_processing=False):
    # create students
    for student in generate_students(students):
        client.put('api/students', data=student)

    # create graders
    for _ in range(max(1, graders)):
        client.post('/api/graders', data={'name': names.get_full_name()})

    generated_exams = []
    for _ in range(exams):
        generated_exams.append(design_exam(app, client, max(1, pages), students, grade, solve, skip_processing))

    return generated_exams


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Create example exam data in the database.')
    parser.add_argument('-d', '--delete', action='store_true', help='delete previous data')
    parser.add_argument('--skip-processing', action='store_true', help='fakes the pdf processing to reduce time. \
                        As a drawback, blanks will not be detected.')
    parser.add_argument('--exams', type=int, default=1, help='number of exams to add')
    parser.add_argument('--pages', type=int, default=3, help='number of pages per exam (min is 1)')
    parser.add_argument('--students', type=int, default=30, help='number of students per exam')
    parser.add_argument('--graders', type=int, default=4, help='number of graders (min is 1)')
    parser.add_argument('--solve', type=int, default=90, help='how much of the solutions to solve (between 0 and 100)')
    parser.add_argument('--grade', type=int, default=60, help='how much of the exam to grade (between 0 and 100). \
                        Notice that only non-blank solutions will be considered for grading.')

    args = parser.parse_args(sys.argv[1:])

    app = init_app(args.delete)

    with app.test_client() as client:
        create_exams(app, client,
                     args.exams,
                     args.pages,
                     args.students,
                     args.graders,
                     args.solve / 100,
                     args.grade / 100,
                     args.skip_processing)
