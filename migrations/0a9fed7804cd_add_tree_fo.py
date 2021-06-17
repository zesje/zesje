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

    connection = op.get_bind()
    rows = connection.execute("SELECT id FROM problem")
    for row in rows:
        root = connection.execute(f"INSERT INTO feedback_option (text, score, problem_id) VALUES ('root', 0, {row.id})")
        connection.execute(f"UPDATE feedback_option SET feedback_option.parent_id = {root.id} WHERE feedback_option.id != {root.id} AND feedback_option.problem_id = {row.id}")


def downgrade():
    with op.batch_alter_table('feedback_option', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_column('parent_id')

