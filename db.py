import os
from datetime import datetime
from collections import namedtuple
import itertools
import subprocess
import shutil
import argparse

import cv2
import zbar
import numpy as np
import pandas
import yaml

from pony.orm import Database, Required, Optional, PrimaryKey, Set, db_session

YAML_VERSION = 0


### Database definition.

db = Database()


# New students may be added throughout the course.
class Student(db.Entity):
    id = PrimaryKey(int)
    first_name = Required(str)
    last_name = Required(str)
    email = Optional(str, unique=True)
    submission = Set('Submission')


# This will be initialized @ app initialization and immutable from then on.
class Grader(db.Entity):
    first_name = Required(str)
    last_name = Required(str)
    graded_solutions = Set('Solution')


# New instances are created when providing a new exam.
class Exam(db.Entity):
    yaml_path = Required(str)
    submissions = Set('Submission')
    problems = Set('Problem')


# Typically created when adding a new exam.
class Submission(db.Entity):
    copy_number = Required(int)
    exam = Required(Exam)
    solutions = Set('Solution')
    source_paths = Set(str)
    student = Optional(Student)
    signature_image_path = Optional(str)


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


def read_yaml(filename):
    with open(filename) as f:
        exam_data = yaml.load(f)

    if exam_data['protocol_version'] != YAML_VERSION:
        raise RuntimeError('Only v{} supported'.format(YAML_VERSION))
    widgets = pandas.DataFrame(exam_data['widgets']).T
    widgets.index.name = 'name'
    qr = widgets[widgets.index.str.contains('qrcode')]
    widgets = widgets[~widgets.index.str.contains('qrcode')]
    return exam_data['name'], qr, widgets


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


def extract_qr(image_path, scale_factor=4):
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
                if version != 'v{}'.format(YAML_VERSION):
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


def rotate_and_get_offset(image_path, extracted_qr, qr_coords):
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
    changed = False
    if (x > w / 2) != (x0 > w / 2):
        image = image[:, ::-1]
        x = w - x
        changed = True
    if (y > h / 2) != (y0 > h / 2):
        image = image[::-1]
        y = h - y
        changed = True

    if changed:
        cv2.imwrite(image_path, image)
    return y-y0, x-x0


def mv_and_get_widgets(image_path, qr, offset, widgets_coords, padding=0.3):
    image = cv2.imread(image_path)
    offset = np.array(offset)
    extension = image_path[image_path.rfind('.'):]
    dpi = guess_dpi(image)
    offset /= dpi
    name, page, submission, _ = qr
    base = os.path.split(image_path)[0]
    target = os.path.join(base, name + '_{}'.format(submission))
    os.makedirs(target, exist_ok=True)
    os.rename(image_path, os.path.join(target, 'page' + str(page) + extension))
    page_widgets = widgets_coords[widgets_coords.page == page].copy()
    page_widgets[['top', 'bottom']] -= offset[1]
    page_widgets[['left', 'right']] -= offset[0]
    for widget in page_widgets.itertuples():
        box = widget.top, widget.bottom, widget.left, widget.right
        filename = os.path.join(target, widget.Index + extension)
        cv2.imwrite(filename, get_box(image, box, padding))
        yield widget.Index, filename


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

def init_db(scanned_pdf, meta_yaml, students='students.csv',
            graders='graders.csv', overwrite=False):
    # Copy the pdf, create the database file.
    exam_name, qr_coords, widget_data = read_yaml(meta_yaml)
    data_dir = exam_name + '_data'
    os.makedirs(data_dir, exist_ok=True)
    pdf_filename = os.path.split(scanned_pdf)[1]
    shutil.copy(scanned_pdf, data_dir)
    db_file = os.path.join(data_dir, exam_name + '.sqlite')
    if not os.path.exists(db_file) or overwrite:
        try:
            os.remove(db_file)
        except OSError:
            pass
        db.bind('sqlite', db_file, create_db=True)
    else:
        db.bind('sqlite', db_file)
    db.generate_mapping(create_tables=True)

    # Create students, graders, problems, and default feedback.
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

        for name in widget_data.index:
            if name == 'studentnr':
                continue
            Problem(name=name)

        # Default feedback (maybe factor out eventually).
        feedback_options = ['Everything correct',
                            'No solution provided']
        problems = Problem.select() ;
        for fb in feedback_options:
            FeedbackOption(text=fb, problems=problems)

    # Process the scanned data
    pdf_to_images(os.path.join(data_dir, pdf_filename))
    images = filter((lambda name: name.endswith('.jpg')),
                    os.listdir(data_dir))
    images = [os.path.join(data_dir, image) for image in images]

    extracted_qrs = [extract_qr(image) for image in images]
    if any(qr[0] != exam_name for qr in extracted_qrs):
        raise RuntimeError('yaml and pdf are from different exams')

    offsets = [rotate_and_get_offset(image, qr, qr_coords)
               for image, qr in zip(images, extracted_qrs)]

    for image, qr_data, offset in zip(images, extracted_qrs, offsets):
        sub_nr = qr_data.sub_nr
        with db_session:
            sub = Submission.get(copy_number=sub_nr) or Submission(copy_number=sub_nr)
            for problem, fname in mv_and_get_widgets(image, qr_data, offset,
                                                     widget_data):
                if problem == 'studentnr':
                    number = get_student_number(fname)
                    sub.student = Student.get(id=int(number))
                    sub.signature_image_path = fname
                else:
                    Solution(problem=Problem.get(name=problem),
                             image_path=fname, submission=sub)


def main():
    parser = argparse.ArgumentParser(description='Create a new exam '
                                     'for grading.')
    parser.add_argument('pdf', help='Scanned exam pdf')
    parser.add_argument('yaml', help='Meta-information about the exam')
    args = parser.parse_args()
    init_db(args.pdf, args.yaml, overwrite=True)

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
