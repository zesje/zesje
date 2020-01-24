"""
Add grading policy to problem table
Add unique constraint to grader name

Revision ID: ea53a654a07e
Revises: ccd9d39aed6f

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine import reflection

# revision identifiers, used by Alembic.
revision = 'ea53a654a07e'
down_revision = 'ccd9d39aed6f'
branch_labels = None
depends_on = None


def _table_has_column(table, column):
    config = op.get_context().config
    engine = sa.engine_from_config(config.get_section(config.config_ini_section), prefix='sqlalchemy.')
    insp = reflection.Inspector.from_engine(engine)
    has_column = False
    for col in insp.get_columns(table):
        if column not in col['name']:
            continue
        has_column = True
    return has_column


def upgrade():
    # Add grading policy to problem
    with op.batch_alter_table('problem', schema=None) as batch_op:
        if not _table_has_column('problem', 'grading_policy'):
            batch_op.add_column(
                sa.Column('grading_policy', sa.Enum('set_nothing', 'set_blank', 'set_single', name='gradingpolicy'),
                          server_default='set_blank', default='set_blank', nullable=False)
            )

    # Set grader name to unique
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

    # op.drop_table('grader_copy')
    op.create_table(
        'grader_copy',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False, unique=True),
        sa.PrimaryKeyConstraint('id')
        )

    op.execute('INSERT INTO grader_copy (id, name)' +
               'SELECT id, name FROM grader')

    op.execute('SET foreign_key_checks=0')
    op.drop_table('grader')
    op.execute('SET foreign_key_checks=1')

    op.rename_table('grader_copy', 'grader')


def downgrade():
    # Remove grading policy from problem
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

    # Remove uniqueness from grader
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
