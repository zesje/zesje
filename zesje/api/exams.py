import hashlib
from io import BytesIO
import os

from flask import current_app, send_file, stream_with_context, Response
from flask.views import MethodView
from flask_login import current_user
from webargs import fields, validate
from sqlalchemy import func

from ._helpers import _shuffle, DBModel, ZesjeValidationError, non_empty_string, use_args, use_kwargs, abort
from .problems import problem_to_data
from ..pdf_generation import exam_dir, exam_pdf_path, _exam_generate_data
from ..pdf_generation import generate_pdfs, generate_single_pdf, generate_zipped_pdfs
from ..pdf_generation import page_is_size, save_with_even_pages
from ..pdf_generation import write_finalized_exam
from ..database import db, Exam, ExamWidget, Submission, FeedbackOption, token_length, ExamLayout
from .submissions import sub_to_data
from .students import student_to_data


def add_blank_feedback(problems):
    """
    Add the blank feedback option to each problem.
    """
    BLANK_FEEDBACK_NAME = current_app.config['BLANK_FEEDBACK_NAME']

    for p in problems:
        # Make blank FO child of the root FO
        db.session.add(FeedbackOption(problem_id=p.id,
                                      text=BLANK_FEEDBACK_NAME,
                                      score=0,
                                      parent=p.root_feedback))

    db.session.commit()


def generate_exam_token(exam_id, exam_name, exam_pdf):
    hasher = hashlib.sha1()
    if exam_pdf:
        hasher.update(exam_pdf)
    hasher.update(f'{exam_id},{exam_name}'.encode('utf-8'))
    return hasher.hexdigest()[0:12]


class Exams(MethodView):

    @use_kwargs({'exam': DBModel(Exam, required=False, load_default=None)})
    @use_kwargs({'only_metadata': fields.Bool(load_default=False)}, location='query')
    def get(self, exam, only_metadata):
        if exam:
            if only_metadata:
                return self._get_single_metadata(exam)
            return self._get_single(exam)
        else:
            return self._get_all()

    @use_kwargs({'exam': DBModel(Exam, required=True, validate_model=[
        lambda exam: not exam.finalized or ZesjeValidationError('Validated exams cannot be deleted', 409)
    ])})
    def delete(self, exam):
        if Submission.query.filter(Submission.exam_id == exam.id).count():
            return dict(status=500, message='Exam is not finalized but already has submissions.'), 500

        # All corresponding solutions, scans and problems are automatically deleted
        db.session.delete(exam)
        db.session.commit()

        return dict(status=200, message="ok"), 200

    def _get_all(self):
        """get list of uploaded exams.

        Returns
        -------
        list of:
            id : int
                exam name
            name : str
                exam ID
            submissions : int
                Number of submissions
        """
        sub_count = {
            result.exam_id: result.sub_count for result in
            db.session.query(Submission.exam_id, func.count(Submission.id).label('sub_count'))
            .group_by(Submission.exam_id).all()
        }
        return [
            {
                'id': ex.id,
                'name': ex.name,
                'layout': ex.layout.name,
                'submissions': sub_count[ex.id] if ex.id in sub_count else 0,
                'finalized': ex.finalized
            }
            for ex in db.session.query(Exam).order_by(Exam.id).all()
        ]

    def _get_single(self, exam):
        """Get detailed information about a single exam

        URL Parameters
        --------------
        exam : int
            exam ID

        Returns
        -------
        id : int
            exam ID
        name : str
            exam name
        submissions
            list of submissions for this exam
        problems
            list of problems defined for this exam
        widgets
            list of widgets in this exam
        """
        submissions = [sub_to_data(sub) for sub in exam.submissions]

        # Sort submissions by selecting those with students assigned, then by
        # student number, then by submission id.
        # TODO: This is a minimal fix of #166, to be replaced later.
        submissions = sorted(
            submissions,
            key=(lambda s: (bool(s['student']) and -s['student']['id'], s['id']))
        )

        return {
            'id': exam.id,
            'name': exam.name,
            'submissions': submissions,
            'problems': [problem_to_data(prob) for prob in exam.problems],  # Sorted by prob.id
            'widgets': [
                {
                    'id': widget.id,
                    'name': widget.name,
                    'x': widget.x,
                    'y': widget.y,
                    'type': widget.type
                } for widget in exam.widgets  # Sorted by widget.id
            ],
            'finalized': exam.finalized,
            'gradeAnonymous': exam.grade_anonymous,
            'layout': exam.layout.name
        }

    def _get_single_metadata(self, exam):
        """ Serves metadata for an exam.
        Shuffles submissions based on the grader ID.

        Parameters
        ----------
        exam : int
            id of exam to get metadata for.

        Returns
        -------
        the exam metadata.

        """
        return {
            'exam_id': exam.id,
            'layout': exam.layout.name,
            'submissions': [
                {
                    'id': sub.id,
                    'student': (
                        {'id': sub.student_id} if exam.grade_anonymous else student_to_data(sub.student)
                        ) if sub.student_id else None
                } for sub in _shuffle(exam.submissions, current_user.id, key_extractor=lambda s: s.id)
            ],
            'problems': [
                {
                    'id': problem.id,
                    'name': problem.name,
                } for problem in exam.problems],
            'gradeAnonymous': exam.grade_anonymous,

        }

    @use_kwargs({'pdf': fields.Field(required=False, load_default=None)}, location='files')
    @use_kwargs({
        'exam_name': fields.Str(required=True, validate=non_empty_string),
        'layout': fields.Enum(ExamLayout, required=True)
    }, location='form')
    def post(self, exam_name, layout, pdf):
        """Add a new exam.

        Parameters
        ----------
        exam_name: str
            name for the exam
        layout: int
            the type of exam to create, one of `ExamLayout` values
        pdf : file, optional
            raw pdf file.

        Returns
        -------
        id : int
            exam ID
        """
        exam_name = exam_name.strip()

        if layout == ExamLayout.templated:
            exam = self._add_templated_exam(exam_name, pdf)
        elif layout == ExamLayout.unstructured:
            exam = self._add_unstructured_exam(exam_name)
        else:
            raise NotImplementedError

        print(f"Added exam {exam.id} (name: {exam_name}, token: {exam.token}) to database")

        return {'id': exam.id}

    def _add_templated_exam(self, exam_name, pdf_data):
        if not pdf_data:
            abort(
                400,
                message='Upload a PDF to add a templated exam.'
            )

        format = current_app.config['PAGE_FORMAT']

        if not page_is_size(pdf_data, current_app.config['PAGE_FORMATS'][format], tolerance=0.01):
            abort(
                400,
                message=f'PDF page size is not {format}.'
            )

        exam = Exam(
            name=exam_name,
            layout=ExamLayout.templated
        )

        exam.widgets = [
            ExamWidget(
                name='student_id_widget',
                x=50,
                y=50,
                exam=exam,
            ),
            ExamWidget(
                name='barcode_widget',
                x=500,
                y=40,
                exam=exam,
            ),
        ]

        db.session.add(exam)
        db.session.commit()  # so exam gets an id
        exam.token = generate_exam_token(exam.id, exam_name, pdf_data.read())
        pdf_data.seek(0)
        db.session.commit()

        save_with_even_pages(exam.id, pdf_data)

        return exam

    def _add_unstructured_exam(self, exam_name):
        exam = Exam(
            name=exam_name,
            layout=ExamLayout.unstructured
        )

        db.session.add(exam)
        db.session.commit()  # so exam gets an id
        exam.token = generate_exam_token(exam.id, exam_name, None)
        db.session.commit()

        os.makedirs(exam_dir(exam.id), exist_ok=True)

        return exam

    @use_kwargs({'exam': DBModel(Exam, required=True)})
    @use_kwargs({
        'finalized': fields.Bool(required=False, load_default=None),
        'grade_anonymous': fields.Bool(required=False, load_default=None)
    }, location='form')
    def put(self, exam, finalized, grade_anonymous):
        if finalized is not None and finalized:
            add_blank_feedback(exam.problems)

            if exam.layout == ExamLayout.templated:
                write_finalized_exam(exam)

            exam.finalized = True
            db.session.commit()
            return dict(status=200, message="ok"), 200
        else:
            return dict(status=403, message='Exam can not be unfinalized'), 403

        if grade_anonymous is not None:
            changed = exam.grade_anonymous != grade_anonymous
            exam.grade_anonymous = grade_anonymous
            db.session.commit()
            return dict(status=200, message="ok", changed=changed), 200

        return dict(status=400, message='One of finalized or anonymous must be present'), 400

    @use_kwargs({'exam': DBModel(Exam, required=True)})
    @use_kwargs({'name': fields.Str(required=True, validate=non_empty_string)}, location='form')
    def patch(self, exam, name):
        """Update the name of an existing exam.

        Parameters
        ----------
        name: str
            name for the exam
        """
        exam.name = name.strip()
        db.session.commit()

        return dict(status=200, message='ok'), 200


ERROR_MSG_PDF = 'PDF is only available in templated exams.'


class ExamSource(MethodView):

    @use_kwargs({'exam': DBModel(Exam, required=True, validate_model=[
        lambda exam: exam.layout == ExamLayout.templated or ZesjeValidationError(ERROR_MSG_PDF, 404)])})
    def get(self, exam):
        return send_file(
            exam_pdf_path(exam.id),
            max_age=0,
            mimetype='application/pdf')


class ExamGeneratedPdfs(MethodView):

    @use_kwargs({'exam': DBModel(Exam, required=True, validate_model=[
        lambda exam: exam.finalized or ZesjeValidationError('Exam must be finalized.', 403),
        lambda exam: exam.layout == ExamLayout.templated or ZesjeValidationError(ERROR_MSG_PDF, 404)])})
    @use_args({
        'copies_start': fields.Int(required=False, load_default=0),
        'copies_end': fields.Int(required=True),
        'type': fields.Str(required=True, validate=validate.OneOf(['pdf', 'zip']))
    }, location='query')
    def get(self, args, exam):
        """Generates the exams with datamatrices and copy numbers.

        A range is given. Ranges should be starting from 1.

        Parameters
        ----------
        copies_start : int
            start of the range of exam pdfs you want to get
        copies_end : int
            end of the range of exam pdfs you want to get
        type: str
            One of "zip", "pdf"
            the pdf option will give a large pdf consisting of concatenated
            exams. Zip will get a zip with all exams as separate files.

        Returns
        -------
        the file : File
            The requested file (zip or pdf)
        """
        copies_start = args['copies_start']
        copies_end = args['copies_end']

        if copies_end < copies_start:
            msg = 'copies_end should be larger than copies_start'
            return dict(status=400, message=msg), 400
        if copies_start <= 0:
            msg = 'copies_start should be larger than 0'
            return dict(status=400, message=msg), 400

        attachment_filename = f'{exam.name}_{copies_start}-{copies_end}.{args["type"]}'
        mimetype = f'application/{args["type"]}'

        if args['type'] == 'pdf':
            output_file = BytesIO()
            generate_single_pdf(exam, copies_start, copies_end, output_file)
            output_file.seek(0)
            return send_file(
                output_file,
                max_age=0,
                download_name=attachment_filename,
                as_attachment=True,
                mimetype=mimetype)
        elif args['type'] == 'zip':
            generator = generate_zipped_pdfs(exam, copies_start, copies_end)
            response = Response(stream_with_context(generator), mimetype=mimetype)
            response.headers['Content-Disposition'] = f'attachment; filename="{attachment_filename}"'
            return response

        return dict(status=400, message='type must be one of ["pdf", "zip"]'), 400


class ExamPreview(MethodView):

    @use_kwargs({'exam': DBModel(Exam, required=True, validate_model=[
        lambda exam: exam.layout == ExamLayout.templated or ZesjeValidationError(ERROR_MSG_PDF, 404)])
    })
    def get(self, exam):
        exam_dir, student_id_widget, barcode_widget, exam_path, cb_data = _exam_generate_data(exam)

        # Generate generic overlay
        _, intermediate_file = next(generate_pdfs(
            exam_pdf_file=exam_path,
            copy_nums=[None],
            id_grid_x=student_id_widget.x,
            id_grid_y=student_id_widget.y,
            cb_data=cb_data
        ))

        # Generate copy overlay
        _, output_file = next(generate_pdfs(
            exam_pdf_file=intermediate_file,
            copy_nums=[1559],
            exam_token="A" * token_length,
            datamatrix_x=barcode_widget.x,
            datamatrix_y=barcode_widget.y,
        ))

        return send_file(
            output_file,
            max_age=0,
            mimetype='application/pdf')
