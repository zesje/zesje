""" Add AUTOINCREMENT keyword to exam table

Revision ID: 6b926be35894
Revises: ea53a654a07e

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '6b926be35894'
down_revision = 'ea53a654a07e'
branch_labels = None
depends_on = None


def upgrade():
    # Initiate a batch operation to force recreation with sqlite_autoincrement
    op.execute('SET foreign_key_checks=0')
    with op.batch_alter_table(
                'exam',
                recreate='always',
                table_kwargs={'sqlite_autoincrement': True}
            ):
        pass
    op.execute('SET foreign_key_checks=1')


def downgrade():
    # Do not remove the AUTOINCREMENT keyword
    pass
