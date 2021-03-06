""" Add tree structure for FeedbackOptions

Revision ID: 0a9fed7804cd
Revises: dccc66cf2881

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0a9fed7804cd'
down_revision = 'dccc66cf2881'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('feedback_option', schema=None) as batch_op:
        batch_op.add_column(sa.Column('parent_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(None, 'feedback_option', ['parent_id'], ['id'])


def downgrade():
    with op.batch_alter_table('feedback_option', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_column('parent_id')
