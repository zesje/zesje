""" Add multiple choice options

Revision ID: b46a2994605b
Revises: 4204f4a83863
Create Date: 2019-05-15 15:41:56.615076
"""
import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = 'b46a2994605b'
down_revision = '4204f4a83863'
branch_labels = None
depends_on = None


def upgrade():
    # Create the multiple choice question table
    op.create_table(
        'mc_option',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('label', sa.String(length=200), nullable=True),
        sa.Column('feedback_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['feedback_id'], ['feedback_option.id'], ),
        sa.ForeignKeyConstraint(['id'], ['widget.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    # Remove the multiple choice question table
    op.drop_table('mc_option')
