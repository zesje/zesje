""" change to mysql

Revision ID: 6ea81b922e15
Revises: 6b926be35894

"""
import os
from alembic import op
import sqlalchemy as sa
from flask import current_app
from zesje.database import db


# revision identifiers, used by Alembic.
revision = '6ea81b922e15'
down_revision = '6b926be35894'
branch_labels = None
depends_on = None

# https://stackoverflow.com/questions/55756491/using-sqlalchemy-to-migrate-databases-sqlite-to-postgres-cloudsql


def upgrade():
    engine_lite = sa.\
        create_engine('sqlite:///' + os.path.join(current_app.config.get('DATA_DIRECTORY'), 'course.sqlite'))

    db.metadata.create_all()

    with engine_lite.connect() as conn_lite:
        for table in db.metadata.sorted_tables:
            data = [dict(row) for row in conn_lite.execute(sa.select(table.c))]
            op.execute(table.insert().values(data))


def downgrade():
    # map all data to sqlite again?
    pass
