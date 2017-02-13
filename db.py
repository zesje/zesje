import os
from datetime import datetime
import subprocess
import shutil
from tempfile import mkdtemp
from xml.dom import minidom
from functools import lru_cache

import cv2
import zbarlight
import numpy as np
import pandas
import yaml
from PIL import Image

from pony.orm import Database, Required, Optional, PrimaryKey, Set, db_session


db = Database()


# this will be initialized @ app initialization and immutable from then on
class Student(db.Entity):
    id = PrimaryKey(int)
    first_name = Required(str)
    last_name = Required(str)
    email = Optional(str, unique=True)
    submission = Optional('Submission')


# this will be initialized @ app initialization and immutable from then on
class Submission(db.Entity):
    solutions = Set('Solution')
    student = Optional(Student)


# this will be initialized @ app initialization and immutable from then on
class Grader(db.Entity):
    first_name = Required(str)
    last_name = Required(str)
    graded_solutions = Set('Solution')


# this will be initialized @ app initialization and immutable from then on
class Problem(db.Entity):
    name = Required(str)
    feedback_options = Set('FeedbackOption')
    solutions = Set('Solution')


# feedback option -- can be shared by multiple problems.
# this means non-duplicate rows for things like 'all correct',
# but means that care must be taken when "updating" and "deleting"
# options from the UI (not yet supported)
class FeedbackOption(db.Entity):
    problems = Set(Problem)
    text = Required(str, unique=True)
    solutions = Set('Solution')


# solution to a single problem
class Solution(db.Entity):
    submission = Required(Submission)
    problem = Required(Problem)
    PrimaryKey(submission, problem)  # enforce uniqueness on this pair

    graded_by = Optional(Grader)  # if null, this has not yet been graded
    graded_at = Optional(datetime)
    image_path = Required(str)
    feedback = Set(FeedbackOption)
    remarks = Optional(str)


@lru_cache()
def studentnr_data(dpi):
    """Prepare data for extracting the student number.

    Returns
    =======
    template : array
        A properly scaled image of the widget with source drawing.
    centers : array of int
        Sorted coordinates of the centers of all circles from the matrix.
    r : int
        Radius of the circles.

    """
    doc = minidom.parse('number_widget.svg')
    centers = np.array([(float(path.getAttribute('cx')),
                         float(path.getAttribute('cy')))
                        for path in doc.getElementsByTagName('ellipse')])
    centers = centers[np.lexsort(centers.T)]
    centers = np.rint((dpi * 4/3 / 90) * centers).astype(int)
    r = next(iter(doc.getElementsByTagName('ellipse'))).getAttribute('rx')
    r = int(float(r) * (dpi * 4/3 / 90))

    subprocess.run(['convert', '-density', '400', 'number_widget.svg',
                    'number_widget.png'])
    template = cv2.imread('number_widget.png')
    os.remove('number_widget.png')
    return template, centers, r


def extract_number(image, dpi):
    template, centers, r = studentnr_data(dpi)
    w, h = template.shape[:2][::-1]
    res = cv2.matchTemplate(image, template, cv2.TM_CCOEFF)
    *_, top_left = cv2.minMaxLoc(res)
    bottom_right = (top_left[0] + w, top_left[1] + h)
    img = image[top_left[1] : bottom_right[1],
              top_left[0] : bottom_right[0]]
    results = []
    for center in centers:
        results.append(np.sum(255 - img[max(center[1] - r, 0)
                                        : center[1] + r,
                                        max(center[0] - r, 0)
                                        : center[0] + r]))
    results = np.array(results)
    digits = (np.argmax(results.reshape(7, 10), axis=1) + 1) % 10
    return int(''.join(map(str, digits)))


def init_db(students='students.csv', graders='graders.csv',
         meta_yaml='test_exam/tussentoets2016-6.yml',
         scanned_pdf='test_exam/sample_data.pdf', overwrite=False):
    YAML_VERSION = 0
    with open(meta_yaml) as f:
        exam_data = yaml.load(f)

    if exam_data['protocol_version'] != YAML_VERSION:
        raise RuntimeError('Only v0 supported')
    db_file = exam_data['name'] + '.sqlite'
    widgets = pandas.DataFrame(exam_data['widgets']).T
    widgets.index.name = 'name'
    widgets = widgets[~widgets.index.str.contains('qrcode')]

    if not os.path.exists(db_file) or overwrite:
        try:
            os.remove(db_file)
        except OSError:
            pass
        db.bind('sqlite', db_file, create_db=True)
    else:
        db.bind('sqlite', db_file)
    db.generate_mapping(create_tables=True)

    with db_session:
        students = pandas.read_csv(students, skipinitialspace=True,
                                   header=None)
        for student_id, first_name, last_name, email in students.values:
            Student(first_name=first_name, last_name=last_name, id=student_id,
                    email=(email if not pandas.isnull(email) else None))

        graders = pandas.read_csv(graders, skipinitialspace=True,
                                  header=None)
        for first_name, last_name in graders.values:
            Grader(first_name=first_name, last_name=last_name)

        for name in widgets.index:
            if name == 'studentnr':
                continue
            Problem(name=name)

        # Default feedback (maybe factor out eventually).
        feedback_options = ['Everything correct',
                            'No solution provided']
        problems = Problem.select() ;
        for fb in feedback_options:
            FeedbackOption(text=fb, problems=problems)

    # Heavy lifting: read the pdf and save all the images

    # Measured offset of coordinates between original and scanned for 300 dpi.
    # Should eventually avoid, and use e.g. cv2.matchTemplate
    delta = np.array([200, 175, -40, 10])
    result_version = 'v' + str(YAML_VERSION)
    tmp = mkdtemp()
    try:
        subprocess.run(['pdfimages', scanned_pdf, tmp + '/'])
        images = os.listdir(tmp)
        for image_path in images:
            image_path = os.path.join(tmp, image_path)
            image = cv2.imread(image_path)
            dpi = int(round(image.shape[0] / 11.6929, -1))
            # zbar is picky about contrast, so we threshold the image.
            # To go sure we try several values of the threshold.
            # Can we do anything better?
            # TODO: don't be lazy and only feed the correct corner to zbar
            for threshold in (200, 150, 220):
                _, thresholded = cv2.threshold(image, threshold, 255,
                                               cv2.THRESH_BINARY)
                code = zbarlight.scan_codes('qrcode',
                                            Image.fromarray(thresholded))
                if code is not None:
                    break
            else:
                raise RuntimeError("Couldn't extract qr code from "
                                   + image_path)
            version, name, page, copy = code[0].decode().split(';')
            if version != result_version:
                raise RuntimeError('Unknown test version,'
                                   ' only {} supported'.format(result_version))
            if name != exam_data['name']:
                raise RuntimeError('yaml and pdf are from different exams')
            target = name + '_data'
            os.makedirs(target, exist_ok=True)

            coords =  (dpi * widgets[widgets.page == int(page)]).astype(int)
            delta_dpi = (delta * dpi / 300).astype(int)
            for widget in coords.itertuples():
                widget_data = image[-widget.top - delta_dpi[0]
                                    : -widget.bottom - delta_dpi[1],
                                    widget.left + delta_dpi[2]
                                    : widget.right + delta_dpi[3]]
                filename = os.path.join(target, widget.Index + copy + '.png')
                cv2.imwrite(filename, widget_data)
                if widget.Index == 'studentnr':
                    # TODO: Hook up the student number to the database.
                    print(extract_number(widget_data, dpi))
                else:
                    with db_session:
                        sub = Submission.get(id=copy) or Submission(id=copy)
                        Solution(problem=Problem.get(name=widget.Index),
                                 image_path=filename, submission=sub)

    finally:
        shutil.rmtree(tmp, ignore_errors=True)

def main():
    init_db(overwrite=True)

    with db_session:
        print('Graders\n' + '-' * 7)
        Grader.select().show()
        print()
        print('Students\n' + '-' * 8)
        Student.select().show()


def use_db(filename='minitest6.sqlite'):
    db.bind('sqlite', filename)
    db.generate_mapping(create_tables=True)


if __name__ == '__main__':
    main()
