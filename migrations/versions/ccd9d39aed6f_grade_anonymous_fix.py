""" Fix anonymous grading column

Revision ID: ccd9d39aed6f
Revises: d6c3d4e65bd6

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ccd9d39aed6f'
down_revision = 'd6c3d4e65bd6'
branch_labels = None
depends_on = None


def upgrade():
    # First remove the grade_anonymous column as the check constraint is missing
    with op.batch_alter_table('exam') as batch_op:
        batch_op.drop_column('grade_anonymous')

    # Then add it again to set it to the right value and add the check constraint
    with op.batch_alter_table('exam') as batch_op:
        batch_op.add_column(sa.Column('grade_anonymous', sa.Boolean(), server_default=sa.false(), nullable=True))


def downgrade():
    # Do not set it back to an incorrect state
    pass
