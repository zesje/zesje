""" db.Models used in the db """

import enum
import os

from flask import current_app
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum
from sqlalchemy import select, join
from flask_sqlalchemy.model import BindMetaMixin, Model
from sqlalchemy.ext.declarative import DeclarativeMeta, declarative_base
from sqlalchemy.orm import backref
from sqlalchemy.orm.session import object_session
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.ext.associationproxy import association_proxy


# Class for NOT automatically determining table names
class NoNameMeta(BindMetaMixin, DeclarativeMeta):
    pass


db = SQLAlchemy(model_class=declarative_base(
    cls=Model, metaclass=NoNameMeta, name='Model'))

token_length = 12


# db.Models #


class Student(db.Model):
    """New students may be added throughout the course."""
    __tablename__ = 'student'
    id = Column(Integer, primary_key=True)
    first_name = Column(Text, nullable=False)
    last_name = Column(Text, nullable=False)
    email = Column(String(320), unique=True)
    submissions = db.relationship('Submission', backref='student', lazy=True)


class Grader(db.Model):
    """Graders can be created by any user at any time, but are immutable once they are created"""
    __tablename__ = 'grader'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    graded_solutions = db.relationship('Solution', backref='graded_by', lazy=True)


class Exam(db.Model):
    """ New instances are created when providing a new exam. """
    __tablename__ = 'exam'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False)
    token = Column(String(token_length), unique=True)
    submissions = db.relationship('Submission', backref='exam', cascade='all', lazy=True)
    problems = db.relationship('Problem', backref='exam', cascade='all', order_by='Problem.id', lazy=True)
    scans = db.relationship('Scan', backref='exam', cascade='all', lazy=True)
    widgets = db.relationship('ExamWidget', backref='exam', cascade='all',
                              order_by='ExamWidget.id', lazy=True)
    finalized = Column(Boolean, default=False, server_default='0')
    grade_anonymous = Column(Boolean, default=False, server_default='0')

    @hybrid_property
    def copies(self):
        # Ordered by copy number, ascending
        return Copy.query.select_from(Exam).\
               join(Exam.submissions).join(Submission.copies).\
               filter(Exam.id == self.id).\
               order_by(Copy.number.asc()).all()
        # TODO For clarity, I rather want this to be something like:
        # [copy for sub in self.submissions for copy in sub.copies]
        # but only use this when all the objects are already loaded
        # and use the query above otherwise.

    # TODO Is this SQL expression really needed?
    @copies.expression
    def copies(cls):
        return select([Copy.id, Copy.number, Copy.submission_id]).\
               select_from(
                   join(Copy, Submission)
               ).\
               where(Submission.exam_id == cls.id)

    # Any migration that alters (and thus recreates) the exam table should explicitly
    # specify this keyword to ensure it will be used for the new table
    __table_args__ = {'sqlite_autoincrement': True}


class Submission(db.Model):
    """Typically created when adding a new exam."""
    __tablename__ = 'submission'
    id = Column(Integer, primary_key=True, autoincrement=True)
    exam_id = Column(Integer, ForeignKey('exam.id'), nullable=False)  # backref exam
    solutions = db.relationship('Solution', backref='submission', cascade='all',
                                order_by='Solution.problem_id', lazy=True)
    copies = db.relationship('Copy', backref='submission', cascade='all', lazy=True)
    student_id = Column(Integer, ForeignKey('student.id'), nullable=True)  # backref student
    validated = Column(Boolean, default=False, server_default='0', nullable=False)


class Copy(db.Model):
    """A copy holding multiple pages"""
    __tablename__ = 'copy'
    id = Column(Integer, primary_key=True, autoincrement=True)
    number = Column(Integer, nullable=False)
    submission_id = Column(Integer, ForeignKey('submission.id'), nullable=False)  # backref submission
    pages = db.relationship('Page', backref='copy', cascade='all', lazy=True)

    exam = association_proxy('submission', 'exam')
    exam_id = association_proxy('submission', 'exam_id')
    student = association_proxy('submission', 'student')
    student_id = association_proxy('submission', 'student_id')
    validated = association_proxy('submission', 'validated')


class Page(db.Model):
    """Page of a copy"""
    __tablename__ = 'page'
    id = Column(Integer, primary_key=True, autoincrement=True)
    path = Column(Text, nullable=False)
    copy_id = Column(Integer, ForeignKey('copy.id'), nullable=False)  # backref copy
    number = Column(Integer, nullable=False)

    @hybrid_property
    def copy_number(self):
        return self.copy.number

    @hybrid_property
    def submission(self):
        return self.copy.submission

    @property
    def abs_path(self):
        return os.path.join(current_app.config['DATA_DIRECTORY'], self.path)


"""
Enum for the grading policy of a problem

The grading policy of a problem means:
    set_nothing: Don't grade automatically
    set_blank:   Automatically grade blank solutions
    set_single:  Automatically grade multiple choice solutions with one selected answer
"""
GradingPolicy = enum.Enum(
    'GradingPolicy',
    'set_nothing set_blank set_single'
)


class Problem(db.Model):
    """this will be initialized @ app initialization and immutable from then on."""
    __tablename__ = 'problem'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False)
    exam_id = Column(Integer, ForeignKey('exam.id'), nullable=False)
    grading_policy = Column('grading_policy', Enum(GradingPolicy), server_default='set_blank',
                            default=GradingPolicy.set_blank, nullable=False)
    feedback_options = db.relationship('FeedbackOption', backref='problem', cascade='all',
                                       order_by='FeedbackOption.id', lazy=True)
    solutions = db.relationship('Solution', backref='problem', cascade='all', lazy=True)
    widget = db.relationship('ProblemWidget', backref='problem', cascade='all', uselist=False, lazy=True)

    @hybrid_property
    def mc_options(self):
        return [feedback_option.mc_option for feedback_option in self.feedback_options if feedback_option.mc_option]


class FeedbackOption(db.Model):
    """feedback option"""
    __tablename__ = 'feedback_option'
    id = Column(Integer, primary_key=True, autoincrement=True)
    problem_id = Column(Integer, ForeignKey('problem.id'))
    text = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    score = Column(Integer, nullable=True)
    mc_option = db.relationship('MultipleChoiceOption', backref=backref('feedback', cascade='all'),
                                cascade='all', uselist=False, lazy=True)


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
            .filter(solution_feedback.c.solution_id == self.id).count()


class Scan(db.Model):
    """Metadata on uploaded PDFs"""
    __tablename__ = 'scan'
    id = Column(Integer, primary_key=True, autoincrement=True)
    exam_id = Column(Integer, ForeignKey('exam.id'), nullable=False)
    name = Column(Text, nullable=False)
    status = Column(Text, nullable=False)
    message = Column(Text)


class Widget(db.Model):
    __tablename__ = 'widget'
    id = Column(Integer, primary_key=True, autoincrement=True)
    # Can be used to distinguish widgets for barcodes, student_id and problems
    name = Column(Text)
    x = Column(Integer, nullable=False)
    y = Column(Integer, nullable=False)
    type = Column(String(20))

    __mapper_args__ = {
        'polymorphic_identity': 'widget',
        'polymorphic_on': type
    }


class MultipleChoiceOption(Widget):
    __tablename__ = 'mc_option'
    id = Column(Integer, ForeignKey('widget.id'), primary_key=True, autoincrement=True)

    label = Column(Text, nullable=True)
    feedback_id = Column(Integer, ForeignKey('feedback_option.id'), nullable=False)

    __mapper_args__ = {
        'polymorphic_identity': 'mcq_widget'
    }


class ExamWidget(Widget):
    __tablename__ = 'exam_widget'
    id = Column(Integer, ForeignKey('widget.id'), primary_key=True, nullable=False)
    exam_id = Column(Integer, ForeignKey('exam.id'), nullable=False)

    __mapper_args__ = {
        'polymorphic_identity': 'exam_widget'
    }

    @property
    def size(self):
        if self.name == 'student_id_widget':
            fontsize = current_app.config['ID_GRID_FONT_SIZE']
            margin = current_app.config['ID_GRID_MARGIN']
            digits = current_app.config['ID_GRID_DIGITS']
            mark_box_size = current_app.config['ID_GRID_BOX_SIZE']
            text_box_width, text_box_height = current_app.config['ID_GRID_TEXT_BOX_SIZE']

            return ((digits + 1) * (fontsize + margin) + 4 * margin + text_box_width,
                    (fontsize + margin) * 11 + mark_box_size)
        elif self.name == 'barcode_widget':
            matrix_box = current_app.config['COPY_NUMBER_MATRIX_BOX_SIZE']
            fontsize = current_app.config['COPY_NUMBER_FONTSIZE']

            return (matrix_box, matrix_box + fontsize + 1)

        raise ValueError(f'Exam widget with name {self.name} has no size defined.')


class ProblemWidget(Widget):
    __tablename__ = 'problem_widget'
    id = Column(Integer, ForeignKey('widget.id'), primary_key=True, nullable=False)
    problem_id = Column(Integer, ForeignKey('problem.id'), nullable=False)
    page = Column(Integer)
    width = Column(Integer)
    height = Column(Integer)

    __mapper_args__ = {
        'polymorphic_identity': 'problem_widget'
    }
