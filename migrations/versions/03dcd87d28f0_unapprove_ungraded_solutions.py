"""Unapprove solutions with empty feedback.

Revision ID: 03dcd87d28f0
Revises: 0a9fed7804cd

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "03dcd87d28f0"
down_revision = "0a9fed7804cd"
branch_labels = None
depends_on = None


def upgrade():
    # removes the grader and grading time from all solutions without any feedback
    conn = op.get_bind()
    conn.execute(
        "UPDATE solution LEFT JOIN "
        "(SELECT solution_id FROM solution_feedback GROUP BY solution_feedback.solution_id) sf "
        "ON solution.id = sf.solution_id "
        "SET solution.grader_id = NULL, solution.graded_at = NULL WHERE sf.solution_id IS NULL"
    )


def downgrade():
    pass
