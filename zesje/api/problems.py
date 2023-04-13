""" REST api for problems """

import os

from flask import current_app
from flask.views import MethodView
from webargs import fields

from ._helpers import DBModel, use_args, use_kwargs, non_empty_string
from .widgets import widget_to_data, normalise_pages
from .feedback import feedback_to_data
from ..database import db, Exam, Problem, ProblemWidget, Solution, GradingPolicy, ExamLayout
from ..pdf_generation import exam_dir
from zesje.pdf_reader import guess_problem_title, get_problem_page


def problem_to_data(problem):
    return {
        "id": problem.id,
        "name": problem.name,
        "feedback": {
            fb.id: feedback_to_data(fb, full_children=False) for fb in problem.feedback_options  # Sorted by fb.id
        },
        "root_feedback_id": problem.root_feedback.id,
        "page": problem.widget.page,
        "widget": widget_to_data(problem.widget),
        "n_graded": Solution.query.filter(Solution.problem_id == problem.id, Solution.grader_id.is_not(None)).count(),
        "grading_policy": problem.grading_policy.name,
        "mc_options": [
            {
                "id": mc_option.id,
                "label": mc_option.label,
                "feedback_id": mc_option.feedback_id,
                "widget": {"name": mc_option.name, "x": mc_option.x, "y": mc_option.y, "type": mc_option.type},
            }
            for mc_option in problem.mc_options
        ],
    }


class Problems(MethodView):
    """List of problems associated with a particular exam_id"""

    @use_kwargs({"problem": DBModel(Problem, required=True)})
    def get(self, problem):
        return problem_to_data(problem)

    @use_args(
        {
            "exam": DBModel(Exam, required=True, data_key="exam_id"),
            "name": fields.Str(required=True),
            "page": fields.Int(required=True),
            "x": fields.Int(required=True),
            "y": fields.Int(required=True),
            "width": fields.Int(required=True),
            "height": fields.Int(required=True),
        },
        location="json",
    )
    def post(self, args):
        """Add a new problem.

        Will error if exam for given id does not exist

        Parameters
        ----------
        exam_id : int
            the exam to which the problem belongs
        name : str
            the name of the problem. If none, the name is guessed from the PDF.
        page : int
            the page where to place the widget
        x, y : int
            left and top coordinates of the widget
        width, height: int
            size of the widget

        Returns
        -------
        dict : the problem
            `id`: the problem id,
            `name`: the problem name,
            `widget_id`: the problem widget id,
            `grading_policy`: the grading policy
        """
        exam = args["exam"]

        if exam.layout == ExamLayout.templated:
            page_size = current_app.config["PAGE_FORMATS"][current_app.config["PAGE_FORMAT"]]
            if not (
                0 <= args["x"] < args["width"] + args["x"] < page_size[0]
                and 0 <= args["y"] < args["height"] + args["y"] < page_size[1]
            ):
                return dict(status=409, message="Problem size exceeds the page size."), 409

        widget = ProblemWidget(
            x=args["x"],
            y=args["y"],
            width=args["width"],
            height=args["height"],
            page=args["page"],
        )

        problem = Problem(
            exam=exam,
            name=args["name"],
            widget=widget,
        )

        # Widget is also added because it is used in problem
        db.session.add(problem)

        # Add solutions for each already existing submission
        for sub in exam.submissions:
            db.session.add(Solution(problem=problem, submission=sub))

        # Commit so problem gets an id
        db.session.commit()
        widget.name = f"problem_{problem.id}"

        if exam.layout == ExamLayout.templated:
            pdf_path = os.path.join(exam_dir(exam.id), "exam.pdf")

            page = get_problem_page(problem, pdf_path)

            if guessed_title := guess_problem_title(problem, page):
                problem.name = guessed_title

            db.session.commit()

        return {
            "id": problem.id,
            "name": problem.name,
            "widget": widget_to_data(widget),
            "grading_policy": problem.grading_policy.name,
            "feedback": {problem.root_feedback.id: feedback_to_data(problem.root_feedback, full_children=False)},
            "root_feedback_id": problem.root_feedback.id,
            "page": problem.widget.page,
            "n_graded": 0,
            "mc_options": [],
        }

    @use_kwargs({"problem": DBModel(Problem, required=True)})
    @use_args(
        {
            "name": fields.Str(required=False, validate=non_empty_string),
            "grading_policy": fields.Enum(GradingPolicy, required=False),
        },
        location="json",
    )
    def patch(self, args, problem):
        """PATCH to a problem

        This method accepts both the problem name and the grading policy.

        problem_id: int
            the problem id to put to
        attr: str
            the attribute (or property) to put to

        Returns
            HTTP 200 on success, 404 if the problem does not exist
        """
        if "name" in args:
            problem.name = args["name"]

        if "grading_policy" in args:
            if problem.exam.layout is not ExamLayout.templated:
                return dict(status=409, message="Cannot modify grading policy on an unstructured exam."), 409
            if args["grading_policy"] == GradingPolicy.set_single and not problem.mc_options:
                return dict(status=409, message="one_answer cannot be set for open answer questions."), 409

            problem.grading_policy = args["grading_policy"]

        db.session.commit()

        return dict(status=200, message="ok"), 200

    @use_kwargs({"problem": DBModel(Problem, required=True)})
    def delete(self, problem):
        """Deletes a problem of an exam if nothing has been graded."""
        if any(sol.is_graded for sol in problem.solutions):
            return dict(status=409, message="Problem has already been graded"), 409

        exam = problem.exam

        # The widget and all associated solutions are automatically deleted
        db.session.delete(problem)
        db.session.commit()

        if exam.layout == ExamLayout.unstructured:
            if normalise_pages([p.widget for p in exam.problems]):
                db.session.commit()

        return dict(status=200, message="ok"), 200
