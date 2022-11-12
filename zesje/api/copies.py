from flask import current_app as app
from flask.views import MethodView
from webargs import fields
from pdfrw import PdfReader

from ._helpers import DBModel, ZesjeValidationError, use_kwargs
from .students import student_to_data
from ..database import db, Exam, Submission, Student, Copy, Solution, ExamLayout
from ..pdf_generation import exam_pdf_path


def copy_to_data(copy):
    sub = copy.submission
    return {
        'number': copy.number,
        'student': student_to_data(sub.student) if sub.student else None,
        'validated': copy.validated
    }


class Copies(MethodView):
    """Getting a list of copies, and assigning students to them."""

    @use_kwargs({
        'exam': DBModel(Exam, required=True),
        'copy_number': fields.Int(required=False)
    })
    def get(self, exam, copy_number=None):
        """get all copies for the given exam

        Parameters
        ----------
        exam : int
            The id of the exam for which copies must be retrievevd
        copy_number : int
            Optionally, the specific copy number to retrieve

        Returns
        -------
        A list of:
            copyID: int
            studentID: int or null
                Student that completed this submission, null if not assigned.
            validated: bool
                True if the assigned student has been validated by a human.
        """
        if copy_number:
            if (copy := Copy.query.filter(Copy.exam == exam,
                                          Copy.number == copy_number).one_or_none()) is None:
                return dict(status=404, message='Copy does not exist.'), 404

            return copy_to_data(copy)

        return [copy_to_data(copy) for copy in exam.copies]  # Ordered by copy number

    @use_kwargs({
        'exam': DBModel(Exam, required=True, validate_model=[lambda exam: exam.layout == ExamLayout.templated or
                ZesjeValidationError('Signatures cannot be validated for unstructured exams.', 422)]),
        'copy_number': fields.Int(required=False, load_default=None)
    })
    @use_kwargs({
        "student": DBModel(Student, required=True, data_key='studentID'),
        'allow_merge': fields.Bool(required=True, data_key='allowMerge')
    }, location='form')
    def put(self, exam, copy_number, student, allow_merge):
        """Assign a student to the given copy.

        Expects a json payload in the format::

            {"studentID": 1234567}


        Parameters
        ----------
        exam : int
        copy_number : int
            The number of the copy. This uniquely identifies
            the copy *within a given exam*.

        """
        if (copy := Copy.query.filter(Copy.number == copy_number,
                                      Copy.exam == exam).one_or_none()) is None:
            return dict(status=404, message='Copy does not exist.'), 404

        old_student = copy.submission.student
        old_submission = copy.submission

        # Does this student have other validated copies?
        new_submission = Submission.query.filter(
            Submission.exam == exam,
            Submission.student == student,
            Submission.validated
        ).one_or_none()

        # Check if we are going to merge feedback
        if (new_submission is not None) and new_submission != old_submission and not allow_merge:
            return dict(status=409,
                        message='Submissions will be merged, but this was not allowed by the request',
                        other_copies=[copy.number for copy in new_submission.copies]), 409

        # If not, find the submission we are going to assign the copy to
        if new_submission is None:
            if student == old_student or len(old_submission.copies) == 1:
                new_submission = old_submission
            else:
                # Create a new empty submission for the student
                new_submission = Submission(exam=exam)
                db.session.add(new_submission)
                for problem in exam.problems:
                    db.session.add(Solution(problem=problem, submission=new_submission))

        copy.submission = new_submission
        new_submission.student = student
        new_submission.validated = True

        if old_submission != new_submission:
            merge_feedback(new_submission, old_submission)
            unapprove_grading(new_submission)

            if len(old_submission.copies) == 0:
                db.session.delete(old_submission)
            else:
                unapprove_grading(old_submission)

        db.session.commit()
        return dict(status=200,
                    message=f'Student {student.id} matched to copy {copy.number}',
                    new_submission_id=new_submission.id), 200


def is_exactly_blank(solution):
    BLANK_FEEDBACK_NAME = app.config['BLANK_FEEDBACK_NAME']
    return all(fb.text == BLANK_FEEDBACK_NAME for fb in solution.feedback) and len(solution.feedback)


def merge_feedback(sub, sub_to_merge):
    BLANK_FEEDBACK_NAME = app.config['BLANK_FEEDBACK_NAME']

    # Ordering is the same since Submission.solutions is ordered by problem_id
    for sol, sol_to_merge in zip(sub.solutions, sub_to_merge.solutions):
        # Merge all feedback options together
        feedback = list(set(sol.feedback + sol_to_merge.feedback))

        # If one of the solutions has feedback other than Blank or no feedback at all,
        # we should remove Blank from the list of feedback options
        both_exactly_blank = is_exactly_blank(sol) and is_exactly_blank(sol_to_merge)
        if not both_exactly_blank:
            feedback = [fb for fb in feedback if fb.text != BLANK_FEEDBACK_NAME]

        sol.feedback = feedback
        sol.remarks = '\n'.join(remarks for remarks in [sol.remarks, sol_to_merge.remarks] if remarks)


def unapprove_grading(sub):
    for sol in sub.solutions:
        sol.graded_by = None
        sol.graded_at = None


class MissingPages(MethodView):

    @use_kwargs({'exam': DBModel(Exam, required=True)})
    def get(self, exam):
        """Compute which copies are missing which pages.

        Parameters
        ----------
        exam : int
            The id of the exam for which the missing pages must be computed.

        Returns
        -------
        Provides a list of:
            copyID: int
            missing_pages: list of ints
        """
        if exam.layout == ExamLayout.templated:
            all_pages = set(range(len(PdfReader(exam_pdf_path(exam.id)).pages)))
        elif exam.layout == ExamLayout.unstructured:
            all_pages = set(problem.widget.page for problem in exam.problems)

        return [
            {
                'number': copy.number,
                'missing_pages': sorted(all_pages - set(page.number for page in copy.pages)),
            } for copy in exam.copies
        ]
