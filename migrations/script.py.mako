""" ${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}

"""
from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}


def upgrade():
    # If you make any changes to the Exam table, please use
    # a batch operation and supply the sqlite_autoincrement
    # argument to preserve the AUTOINCREMENT keyword.
    # See ./6b926be35894_exam_autoincrement.py for a reference.
    ${upgrades if upgrades else "pass"}


def downgrade():
    ${downgrades if downgrades else "pass"}
