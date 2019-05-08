""" db.Models used in the db """

import random
import string

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from flask_sqlalchemy.model import BindMetaMixin, Model
from sqlalchemy.ext.declarative import DeclarativeMeta, declarative_base
from sqlalchemy.orm.session import object_session


# Class for NOT automatically determining table names
class NoNameMeta(BindMetaMixin, DeclarativeMeta):
    pass


db = SQLAlchemy(model_class=declarative_base(
    cls=Model, metaclass=NoNameMeta, name='Model'))

token_length = 12

# Helper functions #
# Have to appear at the top of the file, because otherwise they won't be defined when the db.Models are defined


def _generate_exam_token():
    """Generate an exam token which is not already present in the database. The token consists of 12 randomly generated
    uppercase letters."""
    chars = string.ascii_uppercase

    while True:
        rand_string = ''.join(random.choices(chars, k=token_length))

        if Exam.query.filter(Exam.token == rand_string).first() is None:  # no collision
            return rand_string

# db.Models #


class Student(db.Model):
    """New students may be added throughout the course."""
    __tablename__ = 'student'
    id = Column(Integer, primary_key=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True)
    submissions = db.relationship('Submission', backref='student', lazy=True)


class Grader(db.Model):
    """Graders can be created by any user at any time, but are immutable once they are created"""
    __tablename__ = 'grader'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    graded_solutions = db.relationship('Solution', backref='graded_by', lazy=True)


class Exam(db.Model):
    """ New instances are created when providing a new exam. """
    __tablename__ = 'exam'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    token = Column(String(token_length), unique=True, default=_generate_exam_token)
    submissions = db.relationship('Submission', backref='exam', lazy=True)
    problems = db.relationship('Problem', backref='exam', order_by='Problem.id', lazy=True)
    scans = db.relationship('Scan', backref='exam', lazy=True)
    widgets = db.relationship('ExamWidget', backref='exam', order_by='ExamWidget.id', lazy=True)
    finalized = Column(Boolean, default=False, server_default='f')


class Submission(db.Model):
    """Typically created when adding a new exam."""
    __tablename__ = 'submission'
    id = Column(Integer, primary_key=True, autoincrement=True)
    copy_number = Column(Integer)
    exam_id = Column(Integer, ForeignKey('exam.id'), nullable=False)
    solutions = db.relationship('Solution', backref='submission', order_by='Solution.problem_id', lazy=True)
    pages = db.relationship('Page', backref='submission', lazy=True)
    student_id = Column(Integer, ForeignKey('student.id'), nullable=True)
    signature_validated = Column(Boolean, default=False, server_default='f', nullable=False)


class Page(db.Model):
    """Page of an exam"""
    __tablename__ = 'page'
    id = Column(Integer, primary_key=True, autoincrement=True)
    path = Column(String, nullable=False)
    submission_id = Column(Integer, ForeignKey('submission.id'), nullable=True)
    number = Column(Integer, nullable=False)


class Problem(db.Model):
    """this will be initialized @ app initialization and immutable from then on."""
    __tablename__ = 'problem'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    exam_id = Column(Integer, ForeignKey('exam.id'), nullable=False)
    feedback_options = db.relationship('FeedbackOption', backref='problem', order_by='FeedbackOption.id', lazy=True)
    solutions = db.relationship('Solution', backref='problem', lazy=True)
    widget = db.relationship('ProblemWidget', backref='problem', uselist=False, lazy=True)


class FeedbackOption(db.Model):
    """feedback option"""
    __tablename__ = 'feedback_option'
    id = Column(Integer, primary_key=True, autoincrement=True)
    problem_id = Column(Integer, ForeignKey('problem.id'))
    text = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    score = Column(Integer, nullable=True)


# Table for many to many relationship of FeedbackOption and Solution
solution_feedback = db.Table('solution_feedback',
                             Column('solution_id', Integer, ForeignKey('solution.id'), primary_key=True),
                             Column('feedback_option_id', Integer, ForeignKey('feedback_option.id'), primary_key=True))


class Solution(db.Model):
    """solution to a single problem"""
    __tablename__ = 'solution'
    id = Column(Integer, primary_key=True, autoincrement=True)
    submission_id = Column(Integer, ForeignKey('submission.id'), nullable=False)  # backref submission
    problem_id = Column(Integer, ForeignKey('problem.id'), nullable=False)  # backref problem
    # if grader_id, and thus graded_by, is null, this has not yet been graded
    grader_id = Column(Integer, ForeignKey('grader.id'), nullable=True)  # backref graded_by
    graded_at = Column(DateTime, nullable=True)
    feedback = db.relationship('FeedbackOption', secondary=solution_feedback, backref='solutions', lazy='subquery')
    remarks = Column(Text)

    @property
    def feedback_count(self):
        return object_session(self).query(solution_feedback)\
            .filter(db.text('solution_id == ' + str(self.id))).count()


class Scan(db.Model):
    """Metadata on uploaded PDFs"""
    __tablename__ = 'scan'
    id = Column(Integer, primary_key=True, autoincrement=True)
    exam_id = Column(String, ForeignKey('exam.id'), nullable=False)
    name = Column(String, nullable=False)
    status = Column(String, nullable=False)
    message = Column(String)


class Widget(db.Model):
    __tablename__ = 'widget'
    id = Column(Integer, primary_key=True, autoincrement=True)
    # Can be used to distinguish widgets for barcodes, student_id and problems
    name = Column(String)
    x = Column(Integer, nullable=False)
    y = Column(Integer, nullable=False)
    type = Column(String(20))

    __mapper_args__ = {
        'polymorphic_identity': 'widget',
        'polymorphic_on': type
    }


class MultipleChoiceOption(db.Model):
    __tablename__ = 'mc_option'
    id = Column(Integer, primary_key=True, autoincrement=True)

    x = Column(Integer, nullable=False)
    y = Column(Integer, nullable=False)
    page = Column(Integer, nullable=False)

    label = Column(String, nullable=False)

    problem_id = Column(Integer, ForeignKey('solution.id'))
    feedback_id = Column(Integer, ForeignKey('feedback_option.id'))


class ExamWidget(Widget):
    __tablename__ = 'exam_widget'
    id = Column(Integer, ForeignKey('widget.id'), primary_key=True, nullable=False)
    exam_id = Column(Integer, ForeignKey('exam.id'), nullable=False)

    __mapper_args__ = {
        'polymorphic_identity': 'exam_widget'
    }


class ProblemWidget(Widget):
    __tablename__ = 'problem_widget'
    id = Column(Integer, ForeignKey('widget.id'), primary_key=True, nullable=False)
    problem_id = Column(Integer, ForeignKey('problem.id'), nullable=True)
    page = Column(Integer)
    width = Column(Integer)
    height = Column(Integer)

    __mapper_args__ = {
        'polymorphic_identity': 'problem_widget'
    }
