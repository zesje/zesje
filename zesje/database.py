""" db.Models used in the db """

import enum
import os

from numpy import nan

from flask import current_app
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum
from sqlalchemy import event
from flask_sqlalchemy.model import BindMetaMixin, Model
from sqlalchemy.ext.declarative import DeclarativeMeta, declarative_base
from sqlalchemy.orm import backref, validates
from sqlalchemy.orm.session import object_session
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.sql.schema import MetaData, UniqueConstraint
from sqlalchemy import func

from flask_login import UserMixin, LoginManager
from pathlib import Path


# Class for NOT automatically determining table names
class NoNameMeta(BindMetaMixin, DeclarativeMeta):
    pass


meta = MetaData(naming_convention={
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
})

db = SQLAlchemy(model_class=declarative_base(
    cls=Model, metaclass=NoNameMeta, name='Model', metadata=meta))

token_length = 12

# Initializing login-manager and the user loader function required for login-manager
login_manager = LoginManager()


@login_manager.user_loader
def load_grader(grader_id):
    return Grader.query.get(grader_id)

# db.Models #


class Student(db.Model):
    """New students may be added throughout the course."""
    __tablename__ = 'student'
    id = Column(Integer, primary_key=True)
    first_name = Column(Text, nullable=False)
    last_name = Column(Text, nullable=False)
    email = Column(String(320), unique=True)
    submissions = db.relationship('Submission', backref='student', lazy=True)


class Grader(UserMixin, db.Model):
    """Graders can be created by any user at any time, but are immutable once they are created"""
    __tablename__ = 'grader'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=True)
    oauth_id = Column(String(320), nullable=False, unique=True)
    graded_solutions = db.relationship('Solution', backref='graded_by', lazy=True)
    internal = Column(Boolean, default=False, server_default='0')


ExamLayout = enum.Enum(
    'ExamLayout',
    'templated unstructured'
)


class Exam(db.Model):
    """ New instances are created when providing a new exam. """
    __tablename__ = 'exam'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False)
    token = Column(String(token_length), unique=True)
    submissions = db.relationship('Submission', backref='exam', cascade='all', lazy=True)
    _copies = db.relationship('Copy', backref='_exam', cascade='all', lazy=True)
    problems = db.relationship('Problem', backref='exam', cascade='all', order_by='Problem.id', lazy=True)
    scans = db.relationship('Scan', backref='exam', cascade='all', lazy=True)
    widgets = db.relationship('ExamWidget', backref='exam', cascade='all',
                              order_by='ExamWidget.id', lazy=True)
    finalized = Column(Boolean, default=False, server_default='0')
    grade_anonymous = Column(Boolean, default=False, server_default='0')
    layout = Column('layout', Enum(ExamLayout), server_default='templated', default=ExamLayout.templated,
                    nullable=False)

    @hybrid_property
    def copies(self):
        return self._copies


class Submission(db.Model):
    """Typically created when adding a new exam."""
    __tablename__ = 'submission'
    id = Column(Integer, primary_key=True, autoincrement=True)
    exam_id = Column(Integer, ForeignKey('exam.id'), nullable=False)  # backref exam
    solutions = db.relationship('Solution', backref='submission', cascade='all',
                                order_by='Solution.problem_id', lazy=True)
    copies = db.relationship('Copy', backref='submission', cascade='all',
                             order_by='Copy.number', lazy=True)
    student_id = Column(Integer, ForeignKey('student.id'), nullable=True)  # backref student
    validated = Column(Boolean, default=False, server_default='0', nullable=False)


class Copy(db.Model):
    """A copy holding multiple pages"""
    __tablename__ = 'copy'
    id = Column(Integer, primary_key=True, autoincrement=True)
    number = Column(Integer, nullable=False)
    submission_id = Column(Integer, ForeignKey('submission.id'), nullable=False)  # backref submission
    pages = db.relationship('Page', backref='copy', cascade='all', lazy=True)
    # A copy holds a 'redundant' reference to the exam of its submission
    # to be able to define a unique constraint on (_exam_id, number).
    # This property is read-only and automatically synced on the SQLAlchemy level.
    _exam_id = Column(Integer, ForeignKey('exam.id'), nullable=False)
    UniqueConstraint(_exam_id, number)

    @validates('submission_id', include_backrefs=True)
    def sync_exam_submissison_id(self, key, submission_id):
        """Syncs the assigned exam when the associated submission id changes."""
        if submission_id is not None:
            self._exam_id = Submission.query.get(submission_id).exam_id
        else:
            self._exam_id = None
        return submission_id

    @validates('submission', include_backrefs=True)
    def sync_exam_submissison(self, key, submission):
        """Syncs the assigned exam when the associated submission changes."""
        if submission.exam is not None:
            self._exam = submission.exam

            # Do not flush anything to the database at this point, as we
            # might flush in the wrong order, causing constraints to fail
            with db.session.no_autoflush:
                self._exam_id = submission.exam.id
        return submission

    @hybrid_property
    def exam_id(self):
        return self._exam_id

    @hybrid_property
    def exam(self):
        return self._exam

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
    UniqueConstraint(copy_id, number)

    @hybrid_property
    def copy_number(self):
        return self.copy.number

    @hybrid_property
    def submission(self):
        return self.copy.submission

    @property
    def abs_path(self):
        return os.path.join(current_app.config['DATA_DIRECTORY'], self.path)

    @classmethod
    def retrieve(cls, copy, page_number):
        """Retrieve an existing page or create a new one"""
        return (cls.query.filter(cls.copy == copy, cls.number == page_number).one_or_none() or
                cls(copy=copy, number=page_number))


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

    @property
    def root_feedback(self):
        return next(fb for fb in self.feedback_options if fb.parent_id is None)

    @property
    def max_score(self):
        max_score, = object_session(self).query(func.max(FeedbackOption.score))\
            .filter(FeedbackOption.problem_id == self.id).one()
        return max_score

    @property
    def gradable(self):
        count, max_score = object_session(self).query(func.count(FeedbackOption.id), func.max(FeedbackOption.score))\
            .filter(FeedbackOption.problem_id == self.id).one()
        # There is no possible feedback for this problem (take into account that root always exist).
        return count > 1 and max_score > 0


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
    parent_id = Column(Integer, ForeignKey('feedback_option.id'), nullable=True)
    mut_excl_children = Column(Boolean, nullable=False, server_default='0')
    children = db.relationship("FeedbackOption", backref=backref('parent', remote_side=[id]), cascade='all, delete')

    @property
    def all_descendants(self):
        """Returns all the children recursively"""
        for child in self.children:
            yield child
            yield from child.all_descendants

    @property
    def all_ancestors(self):
        """Returns all the parents recursively except for the `root` option to avoid being graded"""
        next = self.parent
        while next.parent is not None:
            yield next
            next = next.parent
        yield next

    @property
    def siblings(self):
        for sibling in self.parent.children:
            if sibling != self:
                yield sibling


@event.listens_for(Problem, 'after_insert')
def add_root(mapper, connection, problem):
    """Add the root FO to the problem."""
    connection.execute(FeedbackOption.__table__.insert(), text='__root__', score=0, problem_id=problem.id)


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
    feedback = db.relationship('FeedbackOption', secondary=solution_feedback, backref='solutions', lazy=True)
    remarks = Column(Text)

    @property
    def feedback_count(self):
        return object_session(self).query(solution_feedback)\
            .filter(solution_feedback.c.solution_id == self.id).count()

    @property
    def is_graded(self):
        return self.grader_id is not None

    @property
    def score(self):
        score, = object_session(self).query(func.sum(FeedbackOption.score))\
            .join(solution_feedback, FeedbackOption.id == solution_feedback.c.feedback_option_id)\
            .filter(solution_feedback.c.solution_id == self.id).one_or_none()
        return int(score) if score is not None else nan


class Scan(db.Model):
    """Metadata on uploaded PDFs"""
    __tablename__ = 'scan'
    id = Column(Integer, primary_key=True, autoincrement=True)
    exam_id = Column(Integer, ForeignKey('exam.id'), nullable=False)
    name = Column(Text, nullable=False)
    status = Column(Text, nullable=False)
    message = Column(Text)

    @property
    def path(self):
        suffix = Path(self.name).suffix
        scan_dir = Path(current_app.config['SCAN_DIRECTORY'])
        return scan_dir / f'{self.id}{suffix}'


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

    @property
    def exam(self):
        return self.feedback.problem.exam


class ExamWidget(Widget):
    __tablename__ = 'exam_widget'
    id = Column(Integer, ForeignKey('widget.id'), primary_key=True, nullable=False)
    exam_id = Column(Integer, ForeignKey('exam.id'), nullable=False)

    __mapper_args__ = {
        'polymorphic_identity': 'exam_widget'
    }

    @property
    def exam(self):
        return self.exam

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

    @property
    def exam(self):
        return self.problem.exam
