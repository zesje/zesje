""" Copy -> Exam relationship, (Page.copy_id, Page.number) uniqueness, named constraints

Revision ID: 9ddfaa31266b
Revises: 0a9fed7804cd

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '9ddfaa31266b'
down_revision = '0a9fed7804cd'
branch_labels = None
depends_on = None


def index_names(table_name, conn):
    result = conn.execute(f"SHOW INDEX FROM {table_name};")
    return [row['Key_name'] for row in result if row['Key_name'] != 'PRIMARY']


def upgrade():
    conn = op.get_bind()

    # Make sure we can apply the new unique constraints before starting migration
    result = list(conn.execute("SELECT page.copy_id, page.number FROM page "
                               "GROUP BY page.copy_id, page.number HAVING COUNT(*) > 1"))
    if result:
        raise RuntimeError("There are duplicate page entries, not able to run migration.\r\n" +
                           "Duplicate entries (page.copy_id, page.number):\r\n" +
                           ", ".join(str(row) for row in result))

    result = list(conn.execute("SELECT submission.exam_id, copy.number FROM copy "
                               "JOIN submission ON submission.id = copy.submission_id "
                               "GROUP BY submission.exam_id, copy.number HAVING COUNT(*) > 1"))
    if result:
        raise RuntimeError("There are duplicate copy entries, not able to run migration.\r\n" +
                           "Duplicate entries (submission.exam_id, copy.number):\r\n" +
                           ", ".join(str(row) for row in result))

    # Add copy._exam_id column
    with op.batch_alter_table('copy', schema=None) as batch_op:
        batch_op.add_column(sa.Column('_exam_id', sa.Integer(), nullable=False))

    # Populate copy._exam_id with copy.submission.exam_id before defining constraints
    conn.execute(
        'UPDATE copy JOIN submission on submission.id = copy.submission_id SET copy._exam_id = submission.exam_id')

    # Add unique constraint for (copy._exam_id, copy.number)
    # Add foreign key constraint for copy._exam_id
    with op.batch_alter_table('copy', schema=None) as batch_op:
        batch_op.create_unique_constraint(batch_op.f('uq_copy__exam_id'), ['_exam_id', 'number'])
        batch_op.create_foreign_key(batch_op.f('fk_copy__exam_id_exam'), 'exam', ['_exam_id'], ['id'])

    # Add unique constraint for (page.copy_id, page.number)
    with op.batch_alter_table('page', schema=None) as batch_op:
        batch_op.create_unique_constraint(batch_op.f('uq_page_copy_id'), ['copy_id', 'number'])

    # Make sure all constraints have a known name according to the naming convention.
    # We do this by removing all constraints and recreating them with the correct name.

    with op.batch_alter_table('exam', schema=None) as batch_op:
        for index in index_names('exam', conn):
            batch_op.drop_index(index)
        batch_op.create_unique_constraint(batch_op.f('uq_exam_token'), ['token'])

    with op.batch_alter_table('grader', schema=None) as batch_op:
        for index in index_names('grader', conn):
            batch_op.drop_index(index)
        batch_op.create_unique_constraint(batch_op.f('uq_grader_oauth_id'), ['oauth_id'])

    with op.batch_alter_table('student', schema=None) as batch_op:
        for index in index_names('student', conn):
            batch_op.drop_index(index)
        batch_op.create_unique_constraint(batch_op.f('uq_student_email'), ['email'])


def downgrade():
    with op.batch_alter_table('copy', schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f('fk_copy__exam_id_exam'), type_='foreignkey')
        batch_op.drop_constraint(batch_op.f('uq_copy__exam_id'), type_='unique')
        batch_op.drop_column('_exam_id')

    with op.batch_alter_table('page', schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f('uq_page_copy_id'), type_='unique')

    with op.batch_alter_table('student', schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f('uq_student_email'), type_='unique')
        batch_op.create_index('email', ['email'], unique=False)

    with op.batch_alter_table('grader', schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f('uq_grader_oauth_id'), type_='unique')
        batch_op.create_index('oauth_id', ['oauth_id'], unique=False)

    with op.batch_alter_table('exam', schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f('uq_exam_token'), type_='unique')
        batch_op.create_index('token', ['token'], unique=False)
