"""Bundle copies per student

Revision ID: b6e62c576975
Revises: 6b926be35894

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b6e62c576975'
down_revision = '6b926be35894'
branch_labels = None
depends_on = None


def upgrade():
    # TODO Move old data to new schema

    op.create_table(
        'copy',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('number', sa.Integer(), nullable=False),
        sa.Column('submission_id', sa.Integer(), nullable=False),
        sa.Column('signature_validated', sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.ForeignKeyConstraint(['submission_id'], ['submission.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    naming_convention = {
        "fk":
        "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    }

    with op.batch_alter_table('page', schema=None, recreate='always', naming_convention=naming_convention) as batch_op:
        batch_op.add_column(sa.Column('copy_id', sa.Integer(), nullable=False))
        batch_op.create_foreign_key('fk_page_copy_id_copy', 'copy', ['copy_id'], ['id'])

        batch_op.drop_constraint('fk_page_submission_id_submission', type_='foreignkey')
        batch_op.drop_column('submission_id')

    with op.batch_alter_table('submission', schema=None) as batch_op:
        batch_op.drop_column('copy_number')
        batch_op.drop_column('signature_validated')

    # ### end Alembic commands ###


def downgrade():
    # TODO Do we want to support downgrading?
    pass
