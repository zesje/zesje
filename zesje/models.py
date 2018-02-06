""" Models used in the db """
from pony.orm import Database, Required, Optional, PrimaryKey, Set

from datetime import datetime

db = Database()


class Student(db.Entity):
    """ New students may be added throughout the course. """
    id = PrimaryKey(int)
    first_name = Required(str)
    last_name = Required(str)
    email = Optional(str, unique=True)
    submissions = Set('Submission')


class Grader(db.Entity):
    """ This will be initialized @ app initialization and immutable from then on. """
    first_name = Required(str)
    last_name = Required(str)
    graded_solutions = Set('Solution')


class Exam(db.Entity):
    """ New instances are created when providing a new exam. """
    name = Required(str, unique=True)
    yaml_path = Required(str)
    submissions = Set('Submission')
    problems = Set('Problem')
    pdfs = Set('PDF')


class Submission(db.Entity):
    """ Typically created when adding a new exam. """
    copy_number = Required(int)
    exam = Required(Exam)
    solutions = Set('Solution')
    pages = Set('Page')
    student = Optional(Student)
    signature_image_path = Optional(str)
    signature_validated = Required(bool, default=False)


class Page(db.Entity):
    """ Page of an exam """
    path = Required(str)
    submission = Required(Submission)


class Problem(db.Entity):
    """ this will be initialized @ app initialization and immutable from then on. """
    name = Required(str)
    exam = Required(Exam)
    feedback_options = Set('FeedbackOption')
    solutions = Set('Solution')


class FeedbackOption(db.Entity):
    """ feedback option -- can be shared by multiple problems.
    this means non-duplicate rows for things like 'all correct',
    but means that care must be taken when "updating" and "deleting"
    options from the UI (not yet supported)
    """
    problem = Required(Problem)
    text = Required(str)
    description = Optional(str)
    score = Optional(int)
    solutions = Set('Solution')


class Solution(db.Entity):
    """ solution to a single problem """
    submission = Required(Submission)
    problem = Required(Problem)
    PrimaryKey(submission, problem)  # enforce uniqueness on this pair
    graded_by = Optional(Grader)  # if null, this has not yet been graded
    graded_at = Optional(datetime)
    image_path = Required(str)
    feedback = Set(FeedbackOption)
    remarks = Optional(str)


class PDF(db.Entity):
    """Metadata on uploaded PDFs"""
    exam = Required(Exam)
    name = Required(str)
    status = Required(str)
    message = Optional(str)
