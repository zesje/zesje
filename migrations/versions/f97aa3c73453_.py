""" empty message

Revision ID: f97aa3c73453
Revises: 4204f4a83863

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f97aa3c73453'
down_revision = '4204f4a83863'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('mc_option',
                    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
                    sa.Column('x', sa.Integer(), nullable=False),
                    sa.Column('y', sa.Integer(), nullable=False),
                    sa.Column('label', sa.String(), nullable=True),
                    sa.Column('problem_id', sa.Integer(), nullable=False),
                    sa.Column('feedback_id', sa.Integer(), nullable=True),
                    sa.ForeignKeyConstraint(['feedback_id'], ['feedback_option.id'], ),
                    sa.ForeignKeyConstraint(['problem_id'], ['solution.id'], ),
                    sa.PrimaryKeyConstraint('id')
                    )


def downgrade():
    op.drop_table('mc_option')
