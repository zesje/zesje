""" Adds column to problem to specify the grading policy

Revision ID: 02f99246020f
Revises: b46a2994605b

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '02f99246020f'
down_revision = 'b46a2994605b'
branch_labels = None
depends_on = None


def upgrade():
    # Create copy of problem table
    op.create_table(
        'problem_copy',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('exam_id', sa.Integer(), nullable=False),
        sa.Column('grading_policy', sa.Enum('set_nothing', 'set_blank', 'set_blank_single', name='gradingpolicy'),
                  default=1, nullable=False),
        sa.ForeignKeyConstraint(['exam_id'], ['exam.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    conn = op.get_bind()

    old_problems = conn.execute('SELECT id, name, exam_id FROM problem').fetchall()

    grading_policy = "'set_blank'"
    for id, name, exam_id in old_problems:
        # Add quotes for SQLite
        name = "'" + name + "'"
        conn.execute(f'INSERT INTO problem_copy VALUES ({id}, {name}, {exam_id}, {grading_policy})')

    op.drop_table('problem')
    op.rename_table('problem_copy', 'problem')


def downgrade():
    # Create copy of old problem table (without grading policy)
    op.create_table(
        'problem_copy',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('exam_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['exam_id'], ['exam.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Move data from new problem table into old problem table
    op.execute('INSERT INTO problem_copy (id, name, exam_id)' +
               'SELECT id, name, exam_id FROM problem')

    op.drop_table('problem')
    op.rename_table('problem_copy', 'problem')
