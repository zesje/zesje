""" Pony to SQLAlchemy

Revision ID: 4204f4a83863
Revises:

"""
import shutil
from alembic import op
from flask import current_app
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '4204f4a83863'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Make backup of sqlite file since no downgrade is supported
    db_path = current_app.config.get('SQLALCHEMY_DATABASE_URI').replace('sqlite:///', '')
    shutil.copy2(db_path, db_path + '.pony')

    # Remove old indices
    op.drop_index('idx_scan__exam', table_name='Scan')
    op.drop_index('idx_feedbackoption__problem', table_name='FeedbackOption')
    op.drop_index('idx_submission__exam', table_name='Submission')
    op.drop_index('idx_submission__student', table_name='Submission')
    op.drop_index('idx_problem__exam', table_name='Problem')
    op.drop_index('idx_problem__widget', table_name='Problem')
    op.drop_index('idx_page__submission', table_name='Page')
    op.drop_index('idx_widget__exam', table_name='Widget')
    op.drop_index('idx_solution__graded_by', table_name='Solution')
    op.drop_index('idx_solution__problem', table_name='Solution')
    op.drop_index('idx_feedbackoption_solution', table_name='FeedbackOption_Solution')

    # Temporarily prefix old table names with 'Pony'
    table_names = [
        'Exam',
        'FeedbackOption',
        'FeedbackOption_Solution',
        'Grader',
        'Page',
        'Problem',
        'Scan',
        'Solution',
        'Student',
        'Submission',
        'Widget',
    ]
    for table_name in table_names:
        op.rename_table(table_name, 'Pony' + table_name)

    # Create new tables
    op.create_table(
        'exam',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('token', sa.String(length=12), nullable=True),
        sa.Column('finalized', sa.Boolean(), server_default='f', nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token')
    )
    op.create_table(
        'grader',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'student',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('first_name', sa.String(length=120), nullable=False),
        sa.Column('last_name', sa.String(length=120), nullable=False),
        sa.Column('email', sa.String(length=120), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_table(
        'widget',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=120), nullable=True),
        sa.Column('x', sa.Integer(), nullable=False),
        sa.Column('y', sa.Integer(), nullable=False),
        sa.Column('type', sa.String(length=20), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'exam_widget',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('exam_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['exam_id'], ['exam.id'], ),
        sa.ForeignKeyConstraint(['id'], ['widget.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'problem',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('exam_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['exam_id'], ['exam.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'scan',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('exam_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('status', sa.String(length=120), nullable=False),
        sa.Column('message', sa.String(length=120), nullable=True),
        sa.ForeignKeyConstraint(['exam_id'], ['exam.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'submission',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('copy_number', sa.Integer(), nullable=True),
        sa.Column('exam_id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=True),
        sa.Column('signature_validated', sa.Boolean(), server_default='f', nullable=False),
        sa.ForeignKeyConstraint(['exam_id'], ['exam.id'], ),
        sa.ForeignKeyConstraint(['student_id'], ['student.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'feedback_option',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('problem_id', sa.Integer(), nullable=True),
        sa.Column('text', sa.String(length=120), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('score', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['problem_id'], ['problem.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'page',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('path', sa.String(length=120), nullable=False),
        sa.Column('submission_id', sa.Integer(), nullable=True),
        sa.Column('number', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['submission_id'], ['submission.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'problem_widget',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('problem_id', sa.Integer(), nullable=True),
        sa.Column('page', sa.Integer(), nullable=True),
        sa.Column('width', sa.Integer(), nullable=True),
        sa.Column('height', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['id'], ['widget.id'], ),
        sa.ForeignKeyConstraint(['problem_id'], ['problem.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'solution',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('submission_id', sa.Integer(), nullable=False),
        sa.Column('problem_id', sa.Integer(), nullable=False),
        sa.Column('grader_id', sa.Integer(), nullable=True),
        sa.Column('graded_at', sa.DateTime(), nullable=True),
        sa.Column('remarks', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['grader_id'], ['grader.id'], ),
        sa.ForeignKeyConstraint(['problem_id'], ['problem.id'], ),
        sa.ForeignKeyConstraint(['submission_id'], ['submission.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'solution_feedback',
        sa.Column('solution_id', sa.Integer(), nullable=False),
        sa.Column('feedback_option_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['feedback_option_id'], ['feedback_option.id'], ),
        sa.ForeignKeyConstraint(['solution_id'], ['solution.id'], ),
        sa.PrimaryKeyConstraint('solution_id', 'feedback_option_id')
    )

    # Move data from old tables to new tables
    # exam
    op.execute('INSERT INTO exam (id, name, token, finalized) ' +
               'SELECT id, name, token, finalized FROM PonyExam;')

    # widget
    op.execute('INSERT INTO widget (id, name, x, y, type) ' +
               'SELECT id, name, x, y, CASE ' +
               'WHEN classtype = "ExamWidget" THEN "exam_widget" ' +
               'WHEN classtype = "ProblemWidget" THEN "problem_widget" ' +
               'END AS type FROM PonyWidget;')

    # exam_widget
    op.execute('INSERT INTO exam_widget (id, exam_id) ' +
               'SELECT id, exam FROM PonyWidget WHERE classtype = "ExamWidget"')

    # problem_widget
    op.execute('INSERT INTO problem_widget (id, problem_id, page, width, height) ' +
               'SELECT PonyWidget.id, PonyProblem.id, page, width, height FROM PonyWidget ' +
               'JOIN PonyProblem ON PonyWidget.id = PonyProblem.widget WHERE classtype = "ProblemWidget"')

    # feedback_option
    op.execute('INSERT INTO feedback_option (id, problem_id, text, description, score) ' +
               'SELECT id, problem, text, description, score FROM PonyFeedbackOption')

    # grader
    op.execute('INSERT INTO grader (id, name) ' +
               'SELECT id, name FROM PonyGrader')

    # page
    op.execute('INSERT INTO page (id, path, submission_id, number) ' +
               'SELECT id, path, submission, number FROM PonyPage')

    # problem
    op.execute('INSERT INTO problem (id, name, exam_id) ' +
               'SELECT id, name, exam FROM PonyProblem')

    # scan
    op.execute('INSERT INTO scan (id, exam_id, name, status, message)  ' +
               'SELECT id, exam, name, status, message FROM PonyScan')

    # solution
    op.execute('INSERT INTO solution (submission_id, problem_id, grader_id, graded_at, remarks) ' +
               'SELECT submission, problem, graded_by, graded_at, remarks FROM PonySolution')

    # student
    op.execute('INSERT INTO student (id, first_name, last_name, email) ' +
               'SELECT id, first_name, last_name, email FROM PonyStudent')

    # submission
    op.execute('INSERT INTO submission (id, copy_number, exam_id, student_id, signature_validated) ' +
               'SELECT id, copy_number, exam, student, signature_validated FROM PonySubmission')

    # solution_feedback
    op.execute('INSERT INTO solution_feedback (solution_id, feedback_option_id) ' +
               'SELECT PonyFeedbackOption_Solution.feedbackoption, solution.id ' +
               'FROM PonyFeedbackOption_Solution JOIN solution ON ' +
               'solution.submission_id = PonyFeedbackOption_Solution.solution_submission AND ' +
               'solution.problem_id = PonyFeedbackOption_Solution.solution_problem')

    # Remove old tables
    for table_name in table_names:
        op.drop_table('Pony' + table_name)


def downgrade():
    # No support for downgrading to Pony
    pass
