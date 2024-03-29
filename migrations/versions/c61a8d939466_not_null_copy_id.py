""" Set copy id NOT NULL constraint in Page table

Revision ID: c61a8d939466
Revises: ef470a16399e

"""
from alembic import op
from sqlalchemy import Integer

# revision identifiers, used by Alembic.
revision = "c61a8d939466"
down_revision = "ef470a16399e"
branch_labels = None
depends_on = None


def upgrade():
    # alter the page table to add the constraint on the column
    with op.batch_alter_table("page", schema=None) as batch_op:
        batch_op.alter_column("copy_id", existing_type=Integer, nullable=False)


def downgrade():
    pass
