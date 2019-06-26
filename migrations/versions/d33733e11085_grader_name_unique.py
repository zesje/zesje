""" Ensures each grader is uniquely identified by name

Revision ID: d33733e11085
Revises: 02f99246020f

"""
from alembic import op
from flask import current_app
import shutil
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd33733e11085'
down_revision = '02f99246020f'
branch_labels = None
depends_on = None


def backup_db():
    """
    Creates a backup of the current database by making a copy
    of the SQLite file.
    """
    db_url = current_app.config.get('SQLALCHEMY_DATABASE_URI')
    db_path = db_url.replace('sqlite:///', '')

    shutil.copy2(db_path, db_path + '.old')


def upgrade():
    backup_db()

    conn = op.get_bind()

    graders = conn.execute('SELECT id, name FROM grader').fetchall()
    removed_graders = []

    for grader in graders:
        # Check if grader is not deleted already
        if grader in removed_graders:
            continue

        # Get other graders with same name
        other_graders = list(filter(lambda x: x[1] == grader[1] and x != grader, graders))

        for other_grader in other_graders:
            conn.execute(f'UPDATE solution SET grader_id = {grader.id} WHERE solution.grader_id = {other_grader.id}')
            conn.execute(f'DELETE FROM grader WHERE grader.id = {other_grader.id}')

            removed_graders.append(other_grader)

    op.rename_table('grader', 'grader_old')

    # Create copy table and remove data
    op.create_table(
        'grader',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.Text(), nullable=False, unique=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.execute('INSERT INTO grader (id, name)' +
               'SELECT id, name FROM grader_old')

    op.drop_table('grader_old')


def downgrade():
    backup_db()

    op.rename_table('grader', 'grader_old')

    # Add Grader table without unique constraint
    op.create_table(
        'grader',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.Text(), nullable=False, unique=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Move data from old Grader table and delete it
    op.execute('INSERT INTO grader (id, name)' +
               'SELECT id, name FROM grader_old')
    op.drop_table('grader_old')
