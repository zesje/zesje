""" Add exam layout column

Revision ID: 6aaff20fb6c8
Revises: c61a8d939466

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "6aaff20fb6c8"
down_revision = "c61a8d939466"
branch_labels = None
depends_on = None


def upgrade():
    # add the `layout` column with default value `zesje`
    with op.batch_alter_table("exam", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "layout",
                sa.Enum("templated", "unstructured", name="examlayout"),
                server_default="templated",
                nullable=False,
            )
        )


def downgrade():
    # remove the `layout` column
    with op.batch_alter_table("exam", schema=None) as batch_op:
        batch_op.drop_column("layout")
