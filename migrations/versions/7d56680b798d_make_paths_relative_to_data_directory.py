""" Make paths relative to data directory

Revision ID: 7d56680b798d
Revises: 6b926be35894

"""
from alembic import op
from flask import current_app
from os.path import relpath, join


# revision identifiers, used by Alembic.
revision = '7d56680b798d'
down_revision = '6b926be35894'
branch_labels = None
depends_on = None


def upgrade():
    datadir = current_app.config['DATA_DIRECTORY']

    conn = op.get_bind()

    pages = conn.execute('SELECT id, path FROM page').fetchall()

    for page in pages:
        newpath = relpath(page.path, start=datadir)
        conn.execute(f'UPDATE page SET path = "{newpath}" WHERE id = {page.id}')


def downgrade():
    datadir = current_app.config['DATA_DIRECTORY']

    conn = op.get_bind()

    pages = conn.execute('SELECT id, path FROM page').fetchall()

    for page in pages:
        newpath = join(datadir, page.path)
        conn.execute(f'UPDATE page SET path = "{newpath}" WHERE id = {page.id}')
