""" empty message

Revision ID: f7c3bc52d0c7
Revises: 0a9fed7804cd

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'f7c3bc52d0c7'
down_revision = '0a9fed7804cd'
branch_labels = None
depends_on = None


def upgrade():
    # Add copy._exam_id column
    with op.batch_alter_table('copy', schema=None) as batch_op:
        batch_op.add_column(sa.Column('_exam_id', sa.Integer(), nullable=False))

    # Populate copy._exam_id with copy.submission.exam_id before defining constraints
    conn = op.get_bind()
    conn.execute(
        'UPDATE copy JOIN submission on submission.id = copy.submission_id SET copy._exam_id = submission.exam_id')

    # Add unique constraint for (copy._exam_id, copy.number)
    # Add foreign key constraint for copy._exam_id
    with op.batch_alter_table('copy', schema=None) as batch_op:
        batch_op.create_unique_constraint(None, ['_exam_id', 'number'])
        batch_op.create_foreign_key(None, 'exam', ['_exam_id'], ['id'])


def downgrade():
    with op.batch_alter_table('copy', schema=None) as batch_op:
        batch_op.drop_constraint('copy_ibfk_2', type_='foreignkey')
        batch_op.drop_constraint('_exam_id', type_='unique')
        batch_op.drop_column('_exam_id')
