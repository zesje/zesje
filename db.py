import os
from datetime import datetime
from collections import namedtuple, OrderedDict
import itertools
import subprocess
import argparse

import cv2
import zbar
import numpy as np
import pandas
import yaml

from pony import orm
from pony.orm import Database, Required, Optional, PrimaryKey, Set, db_session

### Database definition.

db = Database()


# New students may be added throughout the course.
class Student(db.Entity):
    id = PrimaryKey(int)
    first_name = Required(str)
    last_name = Required(str)
    email = Optional(str, unique=True)
    submissions = Set('Submission')


# This will be initialized @ app initialization and immutable from then on.
class Grader(db.Entity):
    first_name = Required(str)
    last_name = Required(str)
    # email = Optional(str)
    graded_solutions = Set('Solution')


# New instances are created when providing a new exam.
class Exam(db.Entity):
    name = Required(str, unique=True)
    yaml_path = Required(str)
    submissions = Set('Submission')
    problems = Set('Problem')


# Typically created when adding a new exam.
class Submission(db.Entity):
    copy_number = Required(int)
    exam = Required(Exam)
    solutions = Set('Solution')
    pages = Set('Page')
    student = Optional(Student)
    signature_image_path = Optional(str)


class Page(db.Entity):
    path = Required(str)
    submission = Required(Submission)


# this will be initialized @ app initialization and immutable from then on
class Problem(db.Entity):
    name = Required(str)
    exam = Required(Exam)
    feedback_options = Set('FeedbackOption')
    solutions = Set('Solution')


# feedback option -- can be shared by multiple problems.
# this means non-duplicate rows for things like 'all correct',
# but means that care must be taken when "updating" and "deleting"
# options from the UI (not yet supported)
class FeedbackOption(db.Entity):
    problem = Required(Problem)
    text = Required(str)
    description = Optional(str)
    score = Optional(int)
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


### Auxiliary functions dealing with files and images

ExtractedQR = namedtuple('ExtractedQR', ['name', 'page', 'sub_nr', 'coords'])


def pdf_to_images(filename):
    """Extract all images out of a pdf file."""
    subprocess.run(['pdfimages', '-all', filename, filename[:-len('.pdf')]])


def clean_yaml(yml):
    """Clean up the widgets in the raw yaml from the exam latex compilation.

    We must both perform an arithmetic operation, and convert the units to
    points.
    """

    def sp_to_points(value):
        return round(value/2**16/72, 5)

    version = yml['protocol_version']
    if version == 0:
    # Eval is here because we cannot do automatic addition in latex.
        clean_widgets = {name: {key: (sp_to_points(eval(value))
                                      if key != 'page' else value)
                                for key, value in entries.items()}
                         for name, entries in yml['widgets'].items()}
    elif version == 1:
        clean_widgets = [
            {'name': entries['name'],
             'data': {key: (sp_to_points(eval(value))
                            if key not in  ('page', 'name') else value)
                      for key, value in entries['data'].items()}
            }
            for entries in yml['widgets']
        ]
    else:
        raise RuntimeError('YAML version {} is not supported'.format(version))

    return dict(
        name=yml['name'],
        protocol_version=yml['protocol_version'],
        widgets=clean_widgets,
    )


def parse_yaml(yml):
    version = yml['protocol_version']

    if version == 0:
        widgets = pandas.DataFrame(yml['widgets']).T
        widgets.index.name = 'name'
        if widgets.values.dtype == object:
            # probably the yaml has not been processed
            raise RuntimeError('Widget data must be numerical')
        qr = widgets[widgets.index.str.contains('qrcode')]
        widgets = widgets[~widgets.index.str.contains('qrcode')]
        return version, yml['name'], qr, widgets
    elif version == 1:

        def normalize_widgets(wid):
            # widgets are a *list* with fields 'name' and 'data.
            # In version 0 this was a dictionary (i.e. unordered), now it is a
            # list so we can construct an OrderedDict and preserves the ordering.
            # This is important if we want to re-upload and diff the yaml
            # and there are changes to widget names/data.
            wid = OrderedDict((str(w['name']), w['data']) for w in wid)
            df = pandas.DataFrame(wid).T
            df.index.name = 'name'
            return df

        exam_name = yml['name']
        widget_data = yml['widgets']
        qr = normalize_widgets(filter(lambda d: 'qrcode' in str(d['name']), widget_data))
        widgets = normalize_widgets(filter(lambda d: 'qrcode' not in str(d['name']), widget_data))
        return version, exam_name, qr, widgets
    else:
        raise RuntimeError('Version {} not supported'.format(version))


def read_yaml(filename):
    with open(filename) as f:
        return parse_yaml(yaml.load(f))


def guess_dpi(image_array):
    h, w, *_ = image_array.shape
    dpi = np.round(np.array([h, w]) / (297, 210) * 25.4, -1)
    if dpi[0] != dpi[1]:
        raise ValueError("The image doesn't appear to be A4.")
    return dpi[0]


def get_box(image_array, box, padding):
    """Extract a subblock from an array corresponding to a scanned A4 page.

    Parameters:
    -----------
    image_array : 2D or 3D array
        The image source.
    box : 4 floats (top, bottom, left, right)
        Coordinates of the bounding box in inches. By due to differing
        traditions, box coordinates are counted from the bottom left of the
        image, while image array coordinates are from the top left.
    padding : float
        Padding around box borders in inches.
    """
    h, w, *_ = image_array.shape
    dpi = guess_dpi(image_array)
    box = np.array(box)
    box += (padding, -padding, -padding, padding)
    box = (np.array(box) * dpi).astype(int)
    top, bottom = min(h, box[0]), max(0, box[1])
    left, right = max(0, box[2]), min(w, box[3])
    return image_array[-top:-bottom, left:right]


def extract_qr(image_path, yaml_version, scale_factor=4):
    image = cv2.imread(image_path,
                       cv2.IMREAD_GRAYSCALE)[::scale_factor, ::scale_factor]
    if image.shape[0] < image.shape[1]:
        image = image.T
    # Varied thresholds because zbar is picky about contrast.
    for threshold in (200, 150, 220):
        thresholded = 255 * (image > threshold)
        # zbar also cares about orientation.
        for direction in itertools.product([1, -1], [1, -1]):
            flipped = thresholded[::direction[0], ::direction[1]]
            scanner = zbar.Scanner()
            results = scanner.scan(flipped.astype(np.uint8))
            if results:
                version, name, page, copy = results[0].data.decode().split(';')
                if version != 'v{}'.format(yaml_version):
                    raise RuntimeError('Yaml format mismatch')
                coords = np.array(results[0].position)
                # zbar doesn't respect array ordering!
                if not np.isfortran(flipped):
                    coords = coords[:, ::-1]
                coords *= direction
                coords %= image.shape
                coords *= scale_factor
                return ExtractedQR(name, int(page), int(copy), coords)
    else:
        raise RuntimeError("Couldn't extract qr code from " + image_path)


def rotate_and_shift(image_path, extracted_qr, qr_coords):
    _, page, _, position = extracted_qr
    image = cv2.imread(image_path)

    if image.shape[0] < image.shape[1]:
        image = np.transpose(image, (1, 0, 2))

    dpi = guess_dpi(image)
    h, w, *_ = image.shape
    qr_widget = qr_coords[qr_coords.page == page]
    box = dpi * qr_widget[['top', 'bottom', 'left', 'right']].values[0]
    y0, x0 = h - np.mean(box[:2]), np.mean(box[2:])
    y, x = np.mean(position, axis=0)
    if (x > w / 2) != (x0 > w / 2):
        image = image[:, ::-1]
        x = w - x
    if (y > h / 2) != (y0 > h / 2):
        image = image[::-1]
        y = h - y

    shift = np.round((y0-y, x0-x)).astype(int)
    shifted_image = np.roll(image, shift[0], axis=0)
    shifted_image = np.roll(shifted_image, shift[1], axis=1)

    cv2.imwrite(image_path, shifted_image)


def get_widget_image(image_path, widget):
    box = (widget.top, widget.bottom, widget.left, widget.right)
    raw_image = get_box(cv2.imread(image_path), box, padding=0.3)
    return cv2.imencode(".jpg", raw_image)[1].tostring()


def get_student_number(image_path):
    """Extract the student number from the image path with the scanned number.

    TODO: all the numerical parameters are guessed and work well on the first
    exam.  Yet, they should be inferred from the scans.
    """
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    _, thresholded = cv2.threshold(image, 150, 255, cv2.THRESH_BINARY)
    thresholded = cv2.bitwise_not(thresholded)

    # Copy the thresholded image.
    im_floodfill = thresholded.copy()

    # Mask used to flood filling.
    # Notice the size needs to be 2 pixels than the image.
    h, w, *_ = thresholded.shape
    mask = np.zeros((h+2, w+2), np.uint8)

    # Floodfill from point (0, 0)
    cv2.floodFill(im_floodfill, mask, (0,0), 255);

    # Invert floodfilled image
    im_floodfill_inv = cv2.bitwise_not(im_floodfill)

    # Combine the two images to get the foreground.
    im_out = ~(thresholded | im_floodfill_inv)

    params = cv2.SimpleBlobDetector_Params()
    params.filterByArea = True
    params.minArea = 500
    params.maxArea = 1500
    params.filterByCircularity = True
    params.minCircularity = 0.01
    params.filterByConvexity = True
    params.minConvexity = 0.87
    params.filterByInertia = True
    params.minInertiaRatio = 0.7

    detector = cv2.SimpleBlobDetector_create(params)

    keypoints = detector.detect(im_out)
    centers = np.array(sorted([kp.pt for kp in keypoints])).astype(int)
    right, bottom = np.max(centers, axis=0)
    left, top = np.min(centers, axis=0)
    centers = np.mgrid[left:right:10j, top:bottom:7j].astype(int)
    weights = []
    for center in centers.reshape(2, -1).T:
        x, y = center
        r = 12
        weights.append(np.sum(255 - image[y-r:y+r, x-r:x+r]))
    weights = np.array(weights).reshape(10, 7)
    return sum(((np.argmax(weights, axis=0) + 1) % 10)[::-1] * 10**np.arange(7))

### Combining everything: build the database.

def init_db(db_file='course.sqlite', overwrite=False):
    create_db = False
    if not os.path.exists(db_file) or overwrite:
        try:
            os.remove(db_file)
        except OSError:
            pass
        create_db = True

    try:
        db.bind('sqlite', db_file, create_db=create_db)
        db.generate_mapping(create_tables=True)
    except TypeError as exc:  # can raise if db is already bound
        if 'already bound' not in str(exc):
            raise


def add_participants(students='students.csv', graders='graders.csv'):
    init_db()
    with db_session:
        students = pandas.read_csv(students, skipinitialspace=True,
                                   header=None)
        for student_id, first_name, last_name, email in students.values:
            try:
                Student(first_name=first_name, last_name=last_name,
                        id=student_id, email=(email if not pandas.isnull(email)
                                              else None))
            except orm.CacheIndexError:
                pass

        graders = pandas.read_csv(graders, skipinitialspace=True, header=None)
        for first_name, last_name in graders.values:
            try:
                Grader(first_name=first_name, last_name=last_name)
            except orm.CacheIndexError:
                pass


def add_exam(yaml_path):
    init_db()
    _, exam_name, qr_coords, widget_data = read_yaml(yaml_path)
    data_dir = exam_name + '_data'
    os.makedirs(data_dir, exist_ok=True)
    with orm.db_session:
        # init exam
        exam = Exam.get(name=exam_name) or Exam(name=exam_name,
                                                yaml_path=yaml_path)

        # Default feedback (maybe factor out eventually).
        feedback_options = ['Everything correct',
                            'No solution provided']

        for name in widget_data.index:
            if name == 'studentnr':
                continue
            p = Problem(name=name, exam=exam)
            for fb in feedback_options:
                FeedbackOption(text=fb, problem=p)


def update_exam(exam_name, yaml_path):
    _, exam_name, _, widgets = read_yaml(yaml_path)
    new_problem_names = list(name for name in widgets.index
                             if name != 'studentnr')

    with orm.db_session:
        exam = Exam.get(name=exam_name)
        exam.yaml_path = yaml_path
        problems = list(Problem.select(lambda p: p.exam == exam)
                               .order_by(lambda p: p.id))
        for problem, name in zip(problems, new_problem_names):
            problem.name = name


def update_problem_names(exam_name, new_problem_names):
    with orm.db_session:
        exam = Exam.get(name=exam_name)
        problems = list(Problem.select(lambda p: p.exam == exam)
                               .order_by(lambda p: p.id))
        if len(new_problem_names) != len(problems):
            raise ValueError('Number of existing problems and new problem '
                             'names differ.')
        for problem, name in zip(problems, new_problem_names):
            problem.name = str(name)


def process_pdf(pdf_path, meta_yaml):
    init_db()
    # read in metadata
    version, exam_name, qr_coords, widget_data = read_yaml(meta_yaml)
    with db_session:
        exam = Exam.get(name=exam_name)
        if not exam:
            raise RuntimeError('Exam {} does not exist in the database'
                               .format(exam_name))
    # create images
    source_dir, pdf_filename = os.path.split(pdf_path)
    ## shutil.copy(pdf_path, source_dir)
    pdf_to_images(os.path.join(source_dir, pdf_filename))
    images = filter((lambda name: name.endswith('.jpg')),
                    os.listdir(source_dir))
    images =  [os.path.join(source_dir, image) for image in images]
    # verify that copies are from the same exam
    extracted_qrs = [extract_qr(image, version) for image in images]
    if any(qr[0] != exam_name for qr in extracted_qrs):
        for image in images:
            os.remove(image)
        raise RuntimeError('yaml and pdf are from different exams')

    for image, qr in zip(images, extracted_qrs):
        rotate_and_shift(image, qr, qr_coords)


    for image, qr_data in zip(images, extracted_qrs):
        sub_nr = qr_data.sub_nr
        with db_session:
            exam = Exam.get(name=exam_name)
            sub = Submission.get(copy_number=sub_nr, exam=exam) \
                  or Submission(copy_number=sub_nr, exam=exam)
            extension = image[image.rfind('.'):]
            base = os.path.split(image)[0]
            target = os.path.join(base, qr_data.name + '_{}'.format(sub_nr))
            os.makedirs(target, exist_ok=True)
            target_image = os.path.join(target, 'page' + str(qr_data.page)
                                                + extension)
            os.rename(image, target_image)
            Page(path=target_image, submission=sub)
            for problem in widget_data[widget_data.page == qr_data.page].index:
                if problem == 'studentnr':
                    sub.signature_image_path = 'None'
                    try:
                        number = get_student_number(fname)
                        sub.student = Student.get(id=int(number))
                    except Exception:
                        pass  # could not extract student name
                else:
                    prob = Problem.get(name=problem, exam=exam)
                    sol = Solution.get(problem=prob, submission=sub)
                    if sol:
                        sol.image_path = 'None'
                    else:
                        Solution(problem=prob, submission=sub, image_path='None')


def do_everything(scanned_pdf, meta_yaml, students='students.csv',
                  graders='graders.csv', overwrite=False):
    init_db(overwrite=overwrite)
    add_participants(students, graders)
    add_exam(meta_yaml)
    process_pdf(scanned_pdf, meta_yaml)


def main():
    parser = argparse.ArgumentParser(description='Create a new exam '
                                     'for grading.')
    parser.add_argument('--overwrite', action='store_true',
                        help='destroy the existing database')
    parser.add_argument('pdf', help='Scanned exam pdf')
    parser.add_argument('yaml', help='Meta-information about the exam')
    args = parser.parse_args()
    if args.overwrite:
        rsp = input('WARNING: we are going to wipe the database, is this ok? ')
        if not rsp.lower().startswith('y'):
            print('Quitting without overwriting the database')
            exit(0)
        else:
            print('Carrying on...')
    do_everything(args.pdf, args.yaml, overwrite=args.overwrite)

    with db_session:
        print('Graders\n' + '-' * 7)
        Grader.select().show()
        print()
        print('Students\n' + '-' * 8)
        Student.select().show()


def use_db(filename='course.sqlite'):
    db.bind('sqlite', filename)
    db.generate_mapping(create_tables=True)


if __name__ == '__main__':
    main()
