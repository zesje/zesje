"""Add tree structure for FeedbackOptions.

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
        batch_op.create_foreign_key('fk_parent_feedback', 'feedback_option', ['parent_id'], ['id'])

    conn = op.get_bind()
    conn.execute('INSERT INTO feedback_option (text, score, problem_id) '
                 'SELECT "__root__", 0, problem.id FROM problem')
    rows = conn.execute('SELECT id, problem_id FROM feedback_option WHERE feedback_option.text = "__root__"')
    for id, problem_id in rows:
        conn.execute(f'UPDATE feedback_option SET feedback_option.parent_id = {id} '
                     f'WHERE feedback_option.id != {id} AND feedback_option.problem_id = {problem_id}')


def downgrade():
    conn = op.get_bind()
    op.drop_constraint('fk_parent_feedback', 'feedback_option', type_='foreignkey')
    conn.execute('DELETE FROM feedback_option WHERE ISNULL(feedback_option.parent_id)')
    op.drop_column('feedback_option', 'parent_id')
