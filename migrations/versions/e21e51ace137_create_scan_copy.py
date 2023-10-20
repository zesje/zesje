""" create scan_copy

Revision ID: e21e51ace137
Revises: 2cbf733ba928

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'e21e51ace137'
down_revision = '2cbf733ba928'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'scan_copy',
        sa.Column('scan_id', sa.Integer(), sa.ForeignKey("scan.id"), nullable=False),
        sa.Column('copy_id', sa.Integer(), sa.ForeignKey("copy.id"), nullable=False),
        sa.PrimaryKeyConstraint("scan_id", "copy_id"),
    )


def downgrade():
    op.drop_table('scan_copy')
