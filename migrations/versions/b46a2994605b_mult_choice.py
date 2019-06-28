"""
- Save multiple choice question data
- Add grading policy to problem table
- Add unique constraint to grader name

Revision ID: b46a2994605b
Revises: 4204f4a83863
Create Date: 2019-05-15 15:41:56.615076
"""
import sqlalchemy as sa
import shutil
from alembic import op
from flask import current_app


# revision identifiers, used by Alembic.
revision = 'b46a2994605b'
down_revision = '4204f4a83863'
branch_labels = None
depends_on = None


def backup_db():
    """
    Creates a backup of the current database by making a copy
    of the SQLite file.
    """
    db_url = current_app.config.get('SQLALCHEMY_DATABASE_URI')
    db_path = db_url.replace('sqlite:///', '')

    shutil.copy2(db_path, db_path + '.old')


def upgrade():
    backup_db()

    #
    # Create the multiple choice question table
    #
    op.create_table('mc_option',
                    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
                    sa.Column('label', sa.String(), nullable=True),
                    sa.Column('feedback_id', sa.Integer(), nullable=False),
                    sa.ForeignKeyConstraint(['feedback_id'], ['feedback_option.id'], ),
                    sa.ForeignKeyConstraint(['id'], ['widget.id'], ),
                    sa.PrimaryKeyConstraint('id')
                    )

    #
    # Add grading policy to problem
    #
    op.create_table(
        'problem_copy',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('exam_id', sa.Integer(), nullable=False),
        sa.Column('grading_policy', sa.Enum('set_nothing', 'set_blank', 'set_blank_single', name='gradingpolicy'),
                  server_default='set_blank', default='set_blank', nullable=False),
        sa.ForeignKeyConstraint(['exam_id'], ['exam.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.execute('INSERT INTO problem_copy (id, name, exam_id, grading_policy)' +
               'SELECT id, name, exam_id, \'set_blank\' FROM problem')

    op.drop_table('problem')
    op.rename_table('problem_copy', 'problem')

    #
    # Set grader name to unique
    #
    conn = op.get_bind()

    graders = conn.execute('SELECT id, name FROM grader').fetchall()

    for grader in graders:
        # Check if grader is not deleted already
        if not conn.execute(f'SELECT * FROM grader WHERE grader.id  = {grader.id}').fetchall():
            continue

        # Get other graders with same name
        other_graders = list(filter(lambda x: x[1] == grader[1] and x != grader, graders))

        for other_grader in other_graders:
            conn.execute(f'UPDATE solution SET grader_id = {grader.id} WHERE solution.grader_id = {other_grader.id}')
            conn.execute(f'DELETE FROM grader WHERE grader.id = {other_grader.id}')

    op.create_table(
        'grader_copy',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.Text(), nullable=False, unique=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.execute('INSERT INTO grader_copy (id, name)' +
               'SELECT id, name FROM grader')

    op.drop_table('grader')
    op.rename_table('grader_copy', 'grader')


def downgrade():
    #
    # Remove the multiple choice question table
    #
    op.drop_table('mc_option')

    #
    # Remove grading policy from problem
    #
    op.create_table(
        'problem_copy',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('exam_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['exam_id'], ['exam.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.execute('INSERT INTO problem_copy (id, name, exam_id)' +
               'SELECT id, name, exam_id FROM problem')

    op.drop_table('problem')
    op.rename_table('problem_copy', 'problem')

    #
    # Remove uniqueness from grader
    #
    op.create_table(
        'grader_copy',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.Text(), nullable=False, unique=False),
        sa.PrimaryKeyConstraint('id')
    )

    op.execute('INSERT INTO grader_copy (id, name)' +
               'SELECT id, name FROM grader')

    op.drop_table('grader')
    op.rename_table('grader_copy', 'grader')
