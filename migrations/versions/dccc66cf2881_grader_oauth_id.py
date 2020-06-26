""" Added a column oauth_id to store unique ids of oauth providers.

Revision ID: dccc66cf2881
Revises: c61a8d939466

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'dccc66cf2881'
down_revision = '6aaff20fb6c8'
branch_labels = None
depends_on = None


def upgrade():
    # Drop unique constraint for grader name, add unique column oauth_id
    with op.batch_alter_table('grader', schema=None) as batch_op:
        batch_op.add_column(sa.Column('oauth_id', sa.String(length=320), nullable=True))
        batch_op.alter_column('name', existing_type=sa.String(length=100), nullable=True)
        batch_op.drop_index('name')

    conn = op.get_bind()

    # assign oauth id to existing graders
    conn.execute('INSERT INTO grader (id, oauth_id) SELECT id, name FROM grader')

    with op.batch_alter_table('grader', schema=None) as batch_op:
        batch_op.alter_column('oauth_id', existing_type=sa.String(length=320), nullable=False)
        batch_op.create_unique_constraint(None, ['oauth_id'])


def downgrade():
    # drop oauth_id column and add unique constraint to name column and set length to 100
    with op.batch_alter_table('grader', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='unique')
        batch_op.create_index('name', ['name'], unique=True)
        batch_op.alter_column('name',
                              existing_type=mysql.VARCHAR(length=100),
                              nullable=False)
        batch_op.drop_column('oauth_id')
