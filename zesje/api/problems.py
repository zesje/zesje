""" REST api for problems """

import os

from flask_restful import Resource, reqparse, current_app
from ..database import db, Exam, Problem, ProblemWidget, Solution, FeedbackOption, GradingPolicy
from zesje.pdf_reader import guess_problem_title, get_problem_page


class Problems(Resource):
    """ List of problems associated with a particular exam_id """

    post_parser = reqparse.RequestParser()
    post_parser.add_argument('exam_id', type=int, required=True, location='form')
    post_parser.add_argument('name', type=str, required=True, location='form')
    post_parser.add_argument('page', type=int, required=True, location='form')
    post_parser.add_argument('x', type=int, required=True, location='form')
    post_parser.add_argument('y', type=int, required=True, location='form')
    post_parser.add_argument('width', type=int, required=True, location='form')
    post_parser.add_argument('height', type=int, required=True, location='form')
    post_parser.add_argument('grading_policy', type=int, required=True, location='form')

    def post(self):
        """Add a new problem.

        Will error if exam for given id does not exist

        """

        args = self.post_parser.parse_args()

        exam_id = args['exam_id']

        exam = Exam.query.get(exam_id)
        if exam is None:
            msg = f"Exam with id {exam_id} doesn't exist"
            return dict(status=400, message=msg), 400
        else:
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
                grading_policy=GradingPolicy(args['grading_policy'])
            )

            # Widget is also added because it is used in problem
            db.session.add(problem)

            # Add solutions for each already existing submission
            for sub in exam.submissions:
                db.session.add(Solution(problem=problem, submission=sub))

            # Commit so problem gets an id
            db.session.commit()
            widget.name = f'problem_{problem.id}'

            data_dir = current_app.config.get('DATA_DIRECTORY', 'data')
            pdf_path = os.path.join(data_dir, f'{problem.exam_id}_data', 'exam.pdf')

            page = get_problem_page(problem, pdf_path)
            guessed_title = guess_problem_title(problem, page)

            if guessed_title:
                problem.name = guessed_title

            db.session.commit()

            new_feedback_option = FeedbackOption(problem_id=problem.id, text='blank')
            db.session.add(new_feedback_option)
            db.session.commit()

            return {
                'id': problem.id,
                'widget_id': widget.id,
                'problem_name': problem.name
            }

    put_parser = reqparse.RequestParser()
    put_parser.add_argument('name', type=str)
    put_parser.add_argument('grading_policy', type=int)

    def put(self, problem_id):
        """PUT to a problem

        This method accepts both the problem name and the grading policy.

        problem_id: int
            the problem id to put to
        attr: str
            the attribute (or property) to put to

        Returns
            HTTP 200 on success, 404 if problem is invalid
        """

        args = self.put_parser.parse_args()

        problem = Problem.query.get(problem_id)

        if problem is None:
            return dict(status=404, message=f"Problem with id {problem_id} doesn't exist"), 404

        for attr, value in args.items():
            if value is not None:
                setattr(problem, attr, value)

        db.session.commit()

        return dict(status=200, message="ok"), 200

    def delete(self, problem_id):

        problem = Problem.query.get(problem_id)

        if problem is None:
            msg = f"Problem with id {problem_id} doesn't exist"
            return dict(status=404, message=msg), 404
        if any([sol.graded_by is not None for sol in problem.solutions]):
            return dict(status=403, message=f'Problem has already been graded'), 403
        else:
            # The widget and all associated solutions are automatically deleted
            db.session.delete(problem)
            db.session.commit()
            return dict(status=200, message="ok"), 200
