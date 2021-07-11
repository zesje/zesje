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
    # Move and copy data to match the new database structure.
    #
    # Operations like addition/removal of columns or constraints in a table
    # must be done with a batch operation in SQLite. Other SQL backends
    # like MySql or Postgresql support direct alter statements but
    # it is recommended to wrap them also as a batch operation.
    # https://alembic.sqlalchemy.org/en/latest/batch.html
    #
    # It is important to give a name to all constraints to easily remove them.
    ${upgrades if upgrades else "pass"}


def downgrade():
    ${downgrades if downgrades else "pass"}
