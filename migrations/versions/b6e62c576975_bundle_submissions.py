"""Bundle copies per student

Revision ID: b6e62c576975
Revises: 6b926be35894

"""
from alembic import op
import sqlalchemy as sa

from collections import defaultdict


# revision identifiers, used by Alembic.
revision = 'b6e62c576975'
down_revision = '7d56680b798d'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'copy',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('number', sa.Integer(), nullable=False),
        sa.Column('submission_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['submission_id'], ['submission.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'submission_new',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('exam_id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=True),
        sa.Column('validated', sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.ForeignKeyConstraint(['exam_id'], ['exam.id'], ),
        sa.ForeignKeyConstraint(['student_id'], ['student.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'page_new',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('path', sa.Text(), nullable=False),
        sa.Column('copy_id', sa.Integer(), nullable=True),
        sa.Column('number', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['copy_id'], ['copy.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    conn = op.get_bind()

    # Populate new copy table with all the old submissions.
    # Each copy uses the same id as the submission to ensure everything stays linked.
    # The submission_id of copies that belong to a bundled submission will be updated later.
    conn.execute('INSERT INTO copy (id, number, submission_id) ' +
                 'SELECT id, copy_number, id FROM submission')

    bundled_submissions_subquery = '''
    SELECT y.id
    FROM submission AS y
    LEFT OUTER JOIN (
        SELECT x.student_id AS x_student_id, x.exam_id AS x_exam_id
        FROM submission AS x
        WHERE x.signature_validated = 1
        GROUP BY x.exam_id, x.student_id
        HAVING COUNT(*) > 1
    ) AS z
    ON y.student_id = z.x_student_id AND y.exam_id = z.x_exam_id
    WHERE x_student_id IS NOT NULL
    '''

    # Insert all submissions that don't need to be bundled into the new table
    conn.execute('INSERT INTO submission_new (id, exam_id, student_id, validated) ' +
                 'SELECT id, exam_id, student_id, signature_validated ' +
                 'FROM submission ' +
                 f'WHERE submission.id NOT IN ({bundled_submissions_subquery})')

    # Fetch all submissions that need to be bundled
    submissions = conn.execute('SELECT id, copy_number, exam_id, student_id, signature_validated ' +
                               'FROM submission ' +
                               f'WHERE id IN ({bundled_submissions_subquery}) ' +
                               'ORDER BY exam_id, student_id, id').fetchall()

    def bundle_submissions(subs):
        sub_ids = ', '.join(str(s.id) for s in subs)
        solutions = conn.execute('SELECT id, submission_id, problem_id, grader_id, graded_at, remarks ' +
                                 'FROM solution ' +
                                 f'WHERE submission_id IN ({sub_ids}) ' +
                                 'ORDER BY submission_id').fetchall()

        # Merge feedback options of each problem
        solutions_per_problem = defaultdict(list)
        for sol in solutions:
            solutions_per_problem[sol.problem_id].append(sol)
        for problem_id, solutions_of_problem in solutions_per_problem.items():
            sol_to_keep = solutions_of_problem[0]
            duplicate_fbos = False
            for sol_to_delete in solutions_of_problem[1:]:
                try:
                    conn.execute(f'UPDATE solution_feedback SET solution_id = {sol_to_keep.id} ' +
                                 f'WHERE solution_id = {sol_to_delete.id}')
                except sa.exc.IntegrityError:
                    # Unique constraint fails, thus we have a duplicate feedback option
                    duplicate_fbos = True
                    conn.execute(f'UPDATE OR IGNORE solution_feedback SET solution_id = {sol_to_keep.id} ' +
                                 f'WHERE solution_id = {sol_to_delete.id}')

                conn.execute(f'DELETE FROM solution WHERE id = {sol_to_delete.id}')

            # Mark the solution as graded only if all solutions are graded and there are no duplicates
            is_graded = (not duplicate_fbos) and all(s.grader_id is not None for s in solutions_of_problem)
            graded_at = 'NULL'
            grader_id = 'NULL'
            if is_graded:
                graded_solution = next((s for s in solutions_of_problem if s.grader_id is not None))
                graded_at = f'"{graded_solution.graded_at}"'
                grader_id = graded_solution.grader_id

            # Combine all remarks into a single string
            remarks = '\n'.join(sol.remarks for sol in solutions_of_problem
                                if (sol.remarks is not None and sol.remarks != ''))

            conn.execute(f'UPDATE solution SET graded_at = {graded_at}, grader_id = {grader_id}, ' +
                         f'remarks = "{remarks}" '
                         f'WHERE id = {sol_to_keep.id}')

        # Point each copy to the main submission
        sub_to_keep = subs[0]
        for sub_to_delete in subs[1:]:
            conn.execute(f'UPDATE copy SET submission_id = {sub_to_keep.id} ' +
                         f'WHERE submission_id = {sub_to_delete.id}')

        # Add the main submission to the new table
        conn.execute('INSERT INTO submission_new (id, exam_id, student_id, validated) ' +
                     f'VALUES ({sub_to_keep.id}, {sub_to_keep.exam_id}, {sub_to_keep.student_id}, 1)')

    # Bundle all submissions together that need to be bundled
    prev_student = 0
    prev_exam = 0
    prev_submissions = []
    for sub in submissions:
        if prev_student != sub.student_id or prev_exam != sub.exam_id:
            if prev_submissions:
                bundle_submissions(prev_submissions)
                prev_submissions = []

        prev_submissions.append(sub)
        prev_student = sub.student_id
        prev_exam = sub.exam_id

    if prev_submissions:
        bundle_submissions(prev_submissions)

    # Move all pages to new table
    conn.execute('INSERT INTO page_new (id, path, copy_id, number) ' +
                 'SELECT id, path, submission_id, number FROM page')

    op.drop_table('submission')
    op.rename_table('submission_new', 'submission')

    op.drop_table('page')
    op.rename_table('page_new', 'page')


def downgrade():
    # Don't even start...
    raise NotImplementedError('Downgrading to unbundled submission is not supported.')
