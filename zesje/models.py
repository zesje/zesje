""" Models used in the db """
import random
import string

# from https://editor.ponyorm.com/user/zesje/zesje/python
from datetime import datetime
from pony.orm import db_session, Database, Required, Optional, PrimaryKey, Set

db = Database()


# Helper functions #
# Have to appear at the top of the file, because otherwise they won't be defined when the models are defined

def _generate_exam_token():
    """Generate an exam token which is not already present in the database. The token consists of 12 randomly generated
    uppercase letters."""
    length = 12
    chars = string.ascii_uppercase

    while True:
        rand_string = ''.join(random.choices(chars, k=length))

        with db_session:
            if not Exam.select(lambda e: e.token == rand_string).exists():  # no collision
                return rand_string


# Models #

class Student(db.Entity):
    """New students may be added throughout the course."""
    id = PrimaryKey(int)
    first_name = Required(str)
    last_name = Required(str)
    email = Optional(str, unique=True)
    submissions = Set('Submission')


class Grader(db.Entity):
    """This will be initialized @ app initialization and immutable from then on."""
    first_name = Required(str)
    last_name = Required(str)
    graded_solutions = Set('Solution')


class Exam(db.Entity):
    """ New instances are created when providing a new exam. """
    name = Required(str)
    token = Required(str, unique=True, default=_generate_exam_token)
    submissions = Set('Submission')
    problems = Set('Problem')
    scans = Set('PDF')
    widgets = Set('ExamWidget')


class Submission(db.Entity):
    """Typically created when adding a new exam."""
    copy_number = Required(int)
    exam = Required(Exam)
    solutions = Set('Solution')
    pages = Set('Page')
    student = Optional(Student)
    signature_image_path = Optional(str)
    signature_validated = Required(bool, default=False)


class Page(db.Entity):
    """Page of an exam"""
    path = Required(str)
    submission = Required(Submission)


class Problem(db.Entity):
    """this will be initialized @ app initialization and immutable from then on."""
    name = Required(str)
    exam = Required(Exam)
    feedback_options = Set('FeedbackOption')
    solutions = Set('Solution')
    page = Required(int)
    widget = Required('ProblemWidget')


class FeedbackOption(db.Entity):
    """feedback option -- can be shared by multiple problems.
    this means non-duplicate rows for things like 'all correct',
    but means that care must be taken when "updating" and "deleting"
    options from the UI (not yet supported)"""
    problem = Required(Problem)
    text = Required(str)
    description = Optional(str)
    score = Optional(int)
    solutions = Set('Solution')


class Solution(db.Entity):
    """solution to a single problem"""
    submission = Required(Submission)
    problem = Required(Problem)
    graded_by = Optional(Grader)  # if null, this has not yet been graded
    graded_at = Optional(datetime)
    image_path = Required(str)
    feedback = Set(FeedbackOption)
    remarks = Optional(str)
    PrimaryKey(submission, problem)


class PDF(db.Entity):
    """Metadata on uploaded PDFs"""
    exam = Required(Exam)
    name = Required(str)
    status = Required(str)
    message = Optional(str)


class Widget(db.Entity):
    id = PrimaryKey(int, auto=True)
    name = Optional(str)  # Can be used to discretise widgets for barcodes, student_id and problems
    x = Required(int)
    y = Required(int)


class ExamWidget(Widget):
    exam = Required(Exam)


class ProblemWidget(Widget):
    problem = Optional(Problem)
    width = Required(int)
    height = Required(int)
