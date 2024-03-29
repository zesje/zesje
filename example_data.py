#!/usr/bin/env python3

"""
Script to generate a complete database of mock data for testing.
For each exam it generates a pdf with 3 problems per page, where
the number of pages is specified in the arguments.

You can create the sample data by running `python example_data.py -h`:

Usage:
    example_data.py [-h] [-d] [--exams EXAMS] [--pages PAGES]
                       [--students STUDENTS] [--graders GRADERS]
                       [--grade {nothing,partial,all}]

    optional arguments:
      -h, --help                show this help message and exit
      -d, --delete              delete previous data
      --exams (int)             number of exams to add
      --pages (int)             number of pages per exam
      --students (int)          number of students per exam
      --graders (int)           number of graders
      --solve (float)           how much of the solutions to solve (between 0 and 100)
      --grade (float)           how much of the exam to grade (between 0 and 100). Notice that only non-
                                blank solutions will be considered for grading.
      --skip-processing         fakes the pdf processing to reduce time.
                                As a drawback, blanks will not be detected.
      --multiple-copies (float) how much of the students submit multiple copies (between 0 and 100)

"""

import random
import os
import shutil
import sys
import argparse
import time
from datetime import datetime, timedelta, timezone
from io import BytesIO

import lorem
import names
import flask_migrate
from flask import json
from PIL import Image as PILImage, ImageDraw, ImageFont
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from pdfrw import PdfReader, PdfWriter, PageMerge
from tempfile import NamedTemporaryFile
from pathlib import Path
from zipfile import ZipFile

from lorem.text import TextLorem

from zesje.database import db, Exam, Grader, Scan, Submission, Solution, Page, Copy, ExamLayout
from zesje.scans import _process_scan
from zesje.factory import create_app
import zesje.mysql as mysql


if "ZESJE_SETTINGS" not in os.environ:
    os.environ["ZESJE_SETTINGS"] = "../zesje_dev_cfg.py"


lorem_name = TextLorem(srange=(1, 3))
lorem_prob = TextLorem(srange=(2, 5))

pil_font = ImageFont.truetype("tests/data/fonts/Hugohandwriting-Regular.ttf", size=28)


def init_app(delete):
    app = create_app()
    app.config["LOGIN_DISABLED"] = True

    mysql_was_running_before_delete = False
    if os.path.exists(app.config["DATA_DIRECTORY"]) and delete:
        mysql_was_running_before_delete = mysql.is_running(app.config)
        if mysql_was_running_before_delete:
            mysql.stop(app.config)
            time.sleep(5)
        shutil.rmtree(app.config["DATA_DIRECTORY"])

    # ensure directories exists
    os.makedirs(app.config["DATA_DIRECTORY"], exist_ok=True)
    os.makedirs(app.config["SCAN_DIRECTORY"], exist_ok=True)

    mysql_is_created = mysql.create(app.config, allow_exists=True)
    if mysql_is_created:
        time.sleep(2)
    mysql_was_running = mysql.start(app.config, allow_running=True)
    if not mysql_was_running:
        time.sleep(5)  # wait till mysql starts

    # Only create the database from migrations if it was created
    # by this script, otherwise the user should migrate manually
    if delete or mysql_is_created:
        with app.app_context():
            flask_migrate.upgrade(directory="migrations")

    return app, mysql_was_running or mysql_was_running_before_delete


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

    pdf.drawString(problem["x"], problem["y"], problem["question"])
    pdf.rect(problem["x"], problem["y"] - problem["h"] - margin, problem["w"], problem["h"])


def generate_students(students):
    for i in range(students):
        yield {
            "studentID": str(i + 1000000),
            "firstName": names.get_first_name(),
            "lastName": names.get_last_name(),
            "email": str(i + 1000000) + "@fakestudent.tudelft.nl",
        }


def generate_random_page_image(file_path_or_buffer, size):
    img = PILImage.new("RGB", (int(size[0]), int(size[1])), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    margin = 40
    line_height = 24
    groups = random.randint(2, 5)  # groups of sentences in a page
    x = margin + 10

    for group in range(groups):
        y = int((size[1] - 2 * margin) * group / groups) + margin
        for line in range(random.randint(1, 7 - groups)):
            draw.text((x, y + line * line_height), lorem.sentence(), (0, 25, 102), font=pil_font)

    img.save(file_path_or_buffer, format="JPEG")


def _fake_process_pdf(app, exam, scan, pages, student_ids, copies_per_student):
    validate = exam.layout == ExamLayout.unstructured
    copy_number = 0
    for student_id, number_of_copies in zip(student_ids, copies_per_student):
        for _ in range(number_of_copies):
            copy_number += 1
            copy = Copy(number=copy_number)
            scan.copies.append(copy)

            base_copy_path = os.path.join(
                app.config["DATA_DIRECTORY"], f"{exam.id}_data", "submissions", f"{copy_number}"
            )
            os.makedirs(base_copy_path)
            for page in range(pages + 1):
                path = os.path.join(base_copy_path, f"page{page:02d}.jpeg")
                generate_random_page_image(path, A4)
                db.session.add(Page(path=path, copy=copy, number=page))

            sub = Submission(copies=[copy], exam=scan.exam, student_id=student_id, validated=validate)
            db.session.add(sub)

            for problem in scan.exam.problems:
                db.session.add(Solution(problem=problem, submission=sub))

    scan.status = "success"
    scan.message = "Successfully skipped processing."
    db.session.add(scan)
    db.session.commit()


def handle_pdf_processing(app, exam_id, scan_file, pages, student_ids, copies_per_student, skip_processing=False):
    exam = Exam.query.get(exam_id)
    ext = "pdf" if exam.layout == ExamLayout.templated else "zip"
    scan = Scan(exam=exam, name=f"{exam_id}.{ext}", status="processing", message="Waiting...")

    db.session.add(scan)
    db.session.commit()

    scan.name = f"{scan.id}.{ext}"
    db.session.commit()

    path = os.path.join(app.config["SCAN_DIRECTORY"], scan.name)
    with open(path, "wb") as outfile:
        outfile.write(scan_file.read())
        scan_file.seek(0)

    if skip_processing:
        _fake_process_pdf(app, exam, scan, pages, student_ids, copies_per_student)
    else:
        _process_scan(scan_id=scan.id, exam_layout=exam.layout)

    return {"id": scan.id, "name": scan.name, "status": scan.status, "message": scan.message}


def generate_solution(pdf, pages, student_id, problems):
    pdf.setFillColorRGB(0, 0.1, 0.4)

    sID = str(student_id)
    for k in range(7):
        d = int(sID[k])
        pdf.rect(66 + k * 16, int(A4[1]) - 82 - d * 16, 9, 9, fill=1, stroke=0)

    for page in range(pages):
        pdf.setFont("HugoHandwriting", 19)
        pdf.setFillColorRGB(0, 0.1, 0.4)

        for problem in (p for p in problems if p["page"] == page):
            if "mc_options" in problem:
                o = random.choice(problem["mc_options"])
                pdf.rect(o["x"], o["y"] - 8, 9, 8, fill=1, stroke=0)
            else:
                for i in range(random.randint(1, 3)):
                    pdf.drawString(problem["x"] + 20, problem["y"] - 30 - (20 * i), lorem.sentence())

        pdf.showPage()


def solve_problems(pdf_file, pages, student_ids, problems, solve, copies_per_student):
    if solve < 0.01:
        # nothing to solve
        return

    with NamedTemporaryFile() as sol_file:
        pdf = canvas.Canvas(sol_file.name, pagesize=A4)

        for id, number_of_copies in zip(student_ids, copies_per_student):
            for _ in range(number_of_copies):
                generate_solution(pdf, pages, id, [p for p in problems if random.random() < solve])

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


def validate_signatures(client, exam_id, copies, validate):
    for copy in copies:
        number = copy["number"]
        student = copy["student"]
        if not student:
            print(f"\tNo student detected for copy {number} of exam {exam_id}")
        elif random.random() < validate:
            student_id = student["id"]
            client.put(f"/api/copies/{exam_id}/{number}", json={"studentID": student_id, "allowMerge": True})


def grade_problems(client, exam_id, graders, problems, submissions, grade):
    date = datetime.now(timezone.utc)

    for sub in submissions:
        submission_id = sub["id"]

        for prob in sub["problems"]:
            # randomly select the problem if it is not blanck
            if random.random() <= grade and len(prob["feedback"]) == 0:
                fb_data = next(filter(lambda p: p["id"] == prob["problemId"], problems))
                fo, root_id = fb_data["feedback"], fb_data["root_feedback_id"]
                fo = [id for id in fo if int(id) != root_id]
                opt = fo[random.randint(0, len(fo) - 1)]
                client.put(f"/api/solution/{exam_id}/{submission_id}/{prob['problemId']}", json={"id": opt})

                solution = Solution.query.filter(
                    Solution.submission_id == submission_id, Solution.problem_id == prob["problemId"]
                ).one_or_none()

                grader = random.choice(graders)
                solution.grader_id = grader["id"]
                solution.graded_at = date

                dt = timedelta(
                    seconds=int(random.lognormvariate(mu=0.5, sigma=0.4) * 60),
                    hours=random.randint(1, 24) if random.random() < 0.05 else 0,
                )
                date = date - dt
    db.session.commit()


def add_templated_exam(client, pages):
    exam_name = lorem_name.sentence().replace(".", "")
    problems = [
        {
            "question": f"{i + 1}. " + lorem_prob.sentence().replace(".", "?"),
            "page": (i // 3),
            "x": 75,
            "y": int(A4[1]) - 300 - (170 * (i % 3)),
            "w": 450,
            "h": 120,
        }
        for i in range(pages * 3)
    ]

    mc_problems = [
        {
            "question": f"MC{i}. " + lorem_prob.sentence().replace(".", "?"),
            "x": 75,
            "y": int(A4[1]) - 150,
            "w": 300,
            "h": 75,
            "page": i,
            "mc_options": [
                {"name": chr(65 + k), "x": 75 + 20 * (k + 1), "y": int(A4[1]) - 200}
                for k in range(random.randint(2, 5))
            ],
        }
        for i in range(1, pages)
    ]

    with NamedTemporaryFile() as pdf_file:
        generate_exam_pdf(pdf_file, exam_name, pages, problems, mc_problems)
        exam_id = client.post(
            "/api/exams",
            content_type="multipart/form-data",
            data={"exam_name": exam_name, "layout": ExamLayout.templated.name, "pdf": pdf_file},
        ).get_json()["id"]

    return exam_id, problems + mc_problems


def add_unstructured_exam(client, pages):
    exam_name = lorem_name.sentence().replace(".", "")
    problems = [
        {
            "question": f"{i + 1}. " + lorem_prob.sentence().replace(".", "?"),
            "page": (i // 3),
            "x": 0,
            "y": 0,
            "w": 0,
            "h": 0,
        }
        for i in range(pages * 3)
    ]

    exam_id = client.post(
        "/api/exams",
        content_type="multipart/form-data",
        json={"exam_name": exam_name, "layout": ExamLayout.unstructured.name},
    ).get_json()["id"]

    return exam_id, problems


def design_exam(app, client, layout, pages, students, grade, solve, validate, multiple_copies, skip_processing):
    register_fonts()

    if layout == ExamLayout.templated.name:
        exam_id, problems = add_templated_exam(client, pages)
    elif layout == ExamLayout.unstructured.name:
        exam_id, problems = add_unstructured_exam(client, pages)
    else:
        return None

    print("\tDesigning a hard exam.")
    # Create problems
    for problem in problems:
        problem_id = client.post(
            "api/problems",
            json={
                "exam_id": exam_id,
                "name": problem["question"],
                "page": problem["page"],
                # add some padding to x, y, w, h
                "x": problem["x"] - 20,
                "y": int(A4[1]) - problem["y"] - 20,
                "width": problem["w"] + 40,
                "height": problem["h"] + 40,
            },
        ).get_json()["id"]

        is_mcq = "mc_options" in problem
        # Have to put name again, because the endpoint first guesses a name.
        client.put(
            f"api/problems/{problem_id}",
            json={"name": problem["question"], "grading_policy": "set_single" if is_mcq else "set_blank"},
        )

        if is_mcq:
            result = client.get(f"api/problems/{problem_id}")
            parent = json.loads(result.data)["root_feedback_id"]
            fops = []
            for option in problem["mc_options"]:
                resp = client.put(
                    "api/mult-choice/",
                    json={
                        "problem_id": problem_id,
                        "name": option["name"],
                        "label": option["name"],
                        "x": option["x"],
                        "y": int(A4[1]) - option["y"],
                    },
                )
                fops.append((resp.get_json()["feedback_id"], option["name"]))

            correct = random.choice(fops)
            client.patch(f"api/feedback/{problem_id}/{correct[0]}", json={"score": 1})
            client.patch(f"api/feedback/{problem_id}/{parent}", json={"exclusive": True})
        else:
            result = client.get(f"api/problems/{problem_id}")
            root_id = json.loads(result.data)["root_feedback_id"]
            fb_ids = []
            # Add random top-level FOs
            for _ in range(random.randint(2, 10)):
                result = client.post(
                    f"api/feedback/{problem_id}",
                    json={
                        "name": lorem_name.sentence(),
                        "description": (lorem.sentence() if random.choice([True, False]) else ""),
                        "score": random.randint(0, 10),
                        "parentId": root_id,
                    },
                )
                # use return from post to get ids
                data = json.loads(result.data)
                fb_ids.append(data["id"])

            parent_ids_with_children = random.sample(fb_ids, random.randint(2, len(fb_ids)))
            # Add random children to top-level FOs
            for parent_id in parent_ids_with_children:
                for _ in range(random.randint(2, 5)):
                    # get random id from list
                    client.post(
                        f"api/feedback/{problem_id}",
                        json={
                            "name": lorem_name.sentence(),
                            "description": (lorem.sentence() if random.choice([True, False]) else ""),
                            "score": random.randint(0, 10),
                            "parentId": parent_id,
                        },
                    )
                    data = json.loads(result.data)
                    fb_ids.append(data["id"])

            exclusive_parent_ids = random.sample(parent_ids_with_children + [root_id], random.randint(0, 3))
            for id in exclusive_parent_ids:
                client.patch(f"api/feedback/{problem_id}/{id}", json={"exclusive": True})

    client.put(f"api/exams/{exam_id}", json={"finalized": True})

    student_ids = [s["id"] for s in client.get("/api/students").get_json()]
    random.shuffle(student_ids)
    student_ids = student_ids[:students]
    copies_per_student = [2 if random.random() < multiple_copies else 1 for _ in range(students)]

    if layout == ExamLayout.templated.name:
        # Download PDFs
        generated = client.get(
            f"api/exams/{exam_id}/generated_pdfs?copies_start=1&copies_end={sum(copies_per_student)}&type=pdf"
        )

        # Upload submissions
        with NamedTemporaryFile(mode="w+b") as submission_pdf:
            submission_pdf.write(generated.data)
            submission_pdf.seek(0)

            print("\tWaiting for students to solve it.")
            solve_problems(submission_pdf, pages, student_ids, problems, solve, copies_per_student)
            submission_pdf.seek(0)

            print(
                "\tProcessing scans (this may take a while).",
            )
            handle_pdf_processing(app, exam_id, submission_pdf, pages, student_ids, copies_per_student, skip_processing)
    elif layout == ExamLayout.unstructured.name:
        with NamedTemporaryFile(mode="w+b") as submission_zip:
            with ZipFile(submission_zip, "w") as zip:
                for id in student_ids:
                    for page in range(pages):
                        # for now, igonre multiple copies per student
                        buf = BytesIO()
                        generate_random_page_image(buf, A4)
                        zip.writestr(f"{id}-{page}.jpeg", buf.getvalue())
                zip.close()
            submission_zip.seek(0)
            handle_pdf_processing(app, exam_id, submission_zip, pages, student_ids, copies_per_student, skip_processing)

    # Validate signatures
    copies = client.get(f"api/copies/{exam_id}").get_json()
    validate_signatures(client, exam_id, copies, validate)

    submissions = client.get(f"api/submissions/{exam_id}").get_json()
    problems = client.get("/api/exams/" + str(exam_id)).get_json()["problems"]

    graders = client.get("/api/graders").get_json()

    print("\tIt's grading time.")
    grade_problems(client, exam_id, graders, problems, submissions, grade)

    print("\tAll done!")
    return client.get("/api/exams/" + str(exam_id)).get_json()


def create_exams(
    app, client, exams, layout, pages, students, graders, solve, grade, validate, multiple_copies, skip_processing=False
):
    client.get("/api/oauth/start")
    # create graders
    for _ in range(max(1, graders)):
        name = names.get_full_name()
        email = ".".join(name.split(" ")).lower() + "@fake.tudelft.nl"
        grader = Grader(name=name, oauth_id=email)
        db.session.add(grader)
    db.session.commit()

    client.get("/api/oauth/callback")

    # create students
    for student in generate_students(students):
        client.put("api/students", json=student)

    generated_exams = []
    for _ in range(exams):
        generated_exams.append(
            design_exam(
                app, client, layout, max(1, pages), students, grade, solve, validate, multiple_copies, skip_processing
            )
        )

    client.get("/api/oauth/logout")

    return generated_exams


def register_fonts():
    # Font name : file name
    # File name should be the same as internal font name
    fonts = {"HugoHandwriting": "Hugohandwriting-Regular"}

    font_dir = Path.cwd() / "tests" / "data" / "fonts"
    for font_name, font_file in fonts.items():
        font_path_afm = font_dir / (font_file + ".afm")
        font_path_pfb = font_dir / (font_file + ".pfb")

        face = pdfmetrics.EmbeddedType1Face(font_path_afm, font_path_pfb)
        pdfmetrics.registerTypeFace(face)

        font = pdfmetrics.Font(font_name, font_file, "WinAnsiEncoding")
        pdfmetrics.registerFont(font)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create example exam data in the database.")
    parser.add_argument("-d", "--delete", action="store_true", help="delete previous data")
    parser.add_argument(
        "-sp",
        "--skip-processing",
        action="store_true",
        help="fakes the pdf processing to reduce time. As a drawback, blanks will not be detected.",
    )
    parser.add_argument("--exams", type=int, default=1, help="number of exams to add")
    parser.add_argument(
        "--layout",
        type=str,
        default=ExamLayout.templated.name,
        choices=[layout.name for layout in ExamLayout],
        help="the layout of the exams, any of: " + ", ".join(layout.name for layout in ExamLayout),
    )
    parser.add_argument("--pages", type=int, default=3, help="number of pages per exam (min is 1)")
    parser.add_argument("--students", type=int, default=30, help="number of students per exam")
    parser.add_argument("--graders", type=int, default=4, help="number of graders (min is 1)")
    parser.add_argument("--solve", type=int, default=90, help="how much of the solutions to solve (between 0 and 100)")
    parser.add_argument(
        "--validate", type=int, default=90, help="how much of the solutions to validate (between 0 and 100)"
    )
    parser.add_argument(
        "--grade",
        type=int,
        default=60,
        help="how much of the exam to grade (between 0 and 100). \
                        Notice that only non-blank solutions will be considered for grading.",
    )
    parser.add_argument(
        "--multiple-copies",
        type=int,
        default=5,
        help="how much of the students submit multiple copies (between 0 and 100)",
    )

    args = parser.parse_args(sys.argv[1:])

    app, mysql_was_running = init_app(args.delete)

    with app.test_client() as client, app.app_context():
        create_exams(
            app,
            client,
            args.exams,
            args.layout,
            args.pages,
            args.students,
            args.graders,
            args.solve / 100,
            args.grade / 100,
            args.validate / 100,
            args.multiple_copies / 100,
            args.skip_processing,
        )
    if not mysql_was_running:
        mysql.stop(app.config)
