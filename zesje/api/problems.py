""" REST api for problems """

import os

from flask_restful import Resource, reqparse, current_app

from .widgets import widget_to_data, normalise_pages
from ..database import db, Exam, Problem, ProblemWidget, Solution, GradingPolicy, ExamLayout, FeedbackOption
from zesje.pdf_reader import guess_problem_title, get_problem_page


def problem_to_data(problem):
    return {
        'id': problem.id,
        'name': problem.name,
        'feedback': [
            {
                'id': fb.id,
                'name': fb.text,
                'description': fb.description,
                'score': fb.score,
                'used': len(fb.solutions)
            }
            for fb
            in problem.feedback_options  # Sorted by fb.id
        ],
        'page': problem.widget.page,
        'widget': widget_to_data(problem.widget),
        'n_graded': len([sol for sol in problem.solutions if sol.graded_by is not None]),
        'grading_policy': problem.grading_policy.name,
        'mc_options': [
            {
                'id': mc_option.id,
                'label': mc_option.label,
                'feedback_id': mc_option.feedback_id,
                'widget': {
                    'name': mc_option.name,
                    'x': mc_option.x,
                    'y': mc_option.y,
                    'type': mc_option.type
                }
            } for mc_option in problem.mc_options
        ]
    }


class Problems(Resource):
    """ List of problems associated with a particular exam_id """

    def get(self, problem_id):
        if (problem := Problem.query.get(problem_id)) is None:
            return dict(status=404, message=f"Problem with id {problem_id} doesn't exist"), 404

        return problem_to_data(problem)

    post_parser = reqparse.RequestParser()
    post_parser.add_argument('exam_id', type=int, required=True, location='form')
    post_parser.add_argument('name', type=str, required=True, location='form')
    post_parser.add_argument('page', type=int, required=True, location='form')
    post_parser.add_argument('x', type=int, required=True, location='form')
    post_parser.add_argument('y', type=int, required=True, location='form')
    post_parser.add_argument('width', type=int, required=True, location='form')
    post_parser.add_argument('height', type=int, required=True, location='form')

    def post(self):
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

        args = self.post_parser.parse_args()

        exam_id = args['exam_id']

        if (exam := Exam.query.get(exam_id)) is None:
            msg = f"Exam with id {exam_id} doesn't exist"
            return dict(status=400, message=msg), 400

        if exam.layout == ExamLayout.templated:
            page_size = current_app.config['PAGE_FORMATS'][current_app.config['PAGE_FORMAT']]
            if not (0 <= args['x'] < args['width'] + args['x'] < page_size[0]
                    and 0 <= args['y'] < args['height'] + args['y'] < page_size[1]):
                return dict(status=409, message='Problem size exceeds the page size.'), 409

        widget = ProblemWidget(
            x=args['x'],
            y=args['y'],
            width=args['width'],
            height=args['height'],
            page=args['page'],
        )

        problem = Problem(
            exam=exam,
            name=args['name'],
            widget=widget,
        )
        # Widget is also added because it is used in problem
        db.session.add(problem)

        # Create root FO
        root_fo = FeedbackOption(
            problem=problem,
            text="root"
        )
        db.session.add(root_fo)
        # Add solutions for each already existing submission
        for sub in exam.submissions:
            db.session.add(Solution(problem=problem, submission=sub))

        # Commit so problem gets an id
        db.session.commit()
        widget.name = f'problem_{problem.id}'

        if exam.layout == ExamLayout.templated:
            data_dir = current_app.config['DATA_DIRECTORY']
            pdf_path = os.path.join(data_dir, f'{problem.exam_id}_data', 'exam.pdf')

            page = get_problem_page(problem, pdf_path)

            if (guessed_title := guess_problem_title(problem, page)):
                problem.name = guessed_title

            db.session.commit()

        return {
            'id': problem.id,
            'widget_id': widget.id,
            'problem_name': problem.name,
            'grading_policy': problem.grading_policy.name
        }

    put_parser = reqparse.RequestParser()
    put_parser.add_argument('name', type=str)
    put_parser.add_argument('grading_policy', type=str,
                            choices=[policy.name for policy in GradingPolicy])

    def put(self, problem_id):
        """PUT to a problem

        This method accepts both the problem name and the grading policy.

        problem_id: int
            the problem id to put to
        attr: str
            the attribute (or property) to put to

        Returns
            HTTP 200 on success, 404 if the problem does not exist
        """

        args = self.put_parser.parse_args()

        if (problem := Problem.query.get(problem_id)) is None:
            return dict(status=404, message=f"Problem with id {problem_id} doesn't exist"), 404

        for attr, value in args.items():
            if value is not None:
                setattr(problem, attr, value)

        db.session.commit()

        return dict(status=200, message="ok"), 200

    def delete(self, problem_id):
        """Deletes a problem of an exam if nothing has been graded."""
        if (problem := Problem.query.get(problem_id)) is None:
            return dict(status=404, message=f"Problem with id {problem_id} doesn't exist"), 404

        if any([sol.graded_by is not None for sol in problem.solutions]):
            return dict(status=403, message='Problem has already been graded'), 403

        exam = problem.exam

        # The widget and all associated solutions are automatically deleted
        db.session.delete(problem)
        db.session.commit()

        if exam.layout == ExamLayout.unstructured:
            if normalise_pages([p.widget for p in exam.problems]):
                db.session.commit()

        return dict(status=200, message="ok"), 200
