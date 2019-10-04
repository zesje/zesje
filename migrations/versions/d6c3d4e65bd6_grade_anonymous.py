"""
Adds anonymous grading mode to exam

Revision ID: d6c3d4e65bd6
Revises: b46a2994605b

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd6c3d4e65bd6'
down_revision = 'b46a2994605b'
branch_labels = None
depends_on = None


def upgrade():
    # Create gradeAnonymous column
    op.add_column('exam', sa.Column('gradeAnonymous', sa.Boolean(), server_default='f', nullable=True))


def downgrade():
    # Drop gradeAnonymous column
    op.drop_column('exam', 'gradeAnonymous')
