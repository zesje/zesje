""" Add mutually exclusive feedback options.

Revision ID: 2cbf733ba928
Revises: 0a9fed7804cd

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "2cbf733ba928"
down_revision = "9ddfaa31266b"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("feedback_option", schema=None) as batch_op:
        batch_op.add_column(sa.Column("mut_excl_children", sa.Boolean(), server_default="0", nullable=False))


def downgrade():
    with op.batch_alter_table("feedback_option", schema=None) as batch_op:
        batch_op.drop_column("mut_excl_children")
