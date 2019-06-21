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
    # Add grading policy column to Problem
    op.add_column('problem', sa.Column('value',
                                       sa.Enum('set_nothing', 'set_blank', 'set_blank_single', name='gradingpolicy'),
                                       default=1, nullable=True))


def downgrade():
    # Remove grading policy column from Problem
    op.drop_column('problem', 'value')
