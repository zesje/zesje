from flask import current_app
from flask.views import MethodView
from webargs import fields

from ._helpers import DBModel, ZesjeValidationError, ExamNotFinalizedError, use_kwargs
from ..scans import process_scan
from ..database import db, Exam, Scan


def _is_mimetype_allowed(pdf):
    mimetype = pdf.mimetype
    if not (
        mimetype == 'application/pdf' or
        mimetype.startswith('image') or
        mimetype in current_app.config['ZIP_MIME_TYPES']
    ):
        raise ZesjeValidationError('File is not a PDF, ZIP or image.', 400)


class Scans(MethodView):
    """Getting a list of uploaded scans, and uploading new ones."""

    @use_kwargs({'exam': DBModel(Exam, required=True)})
    def get(self, exam):
        """get all uploaded scans for a particular exam.

        Parameters
        ----------
        exam_id : int

        Returns
        -------
        list of:
            name: str
                filename of the uploaded PDF
        """
        return [
            {
                'id': scan.id,
                'name': scan.name,
                'status': scan.status,
                'message': scan.message,
            }
            for scan in exam.scans
        ]

    @use_kwargs({'exam': DBModel(Exam, required=True, validate_model=[
        lambda exam: exam.finalized or ExamNotFinalizedError])})
    @use_kwargs({'file': fields.Field(required=True, validate=_is_mimetype_allowed)}, location='files')
    def post(self, exam, file):
        """Upload a scan PDF

        Parameters
        ----------
        exam_id : int
        pdf : FileStorage

        Returns
        -------
        id : int
        name : str
        status : str
        message : str
        """
        scan = Scan(exam=exam, name=file.filename,
                    status='processing', message='Waiting...')
        db.session.add(scan)
        db.session.commit()

        try:
            file.save(scan.path)
        except Exception:
            scan = Scan.query.get(scan.id)
            if scan is not None:
                db.session.delete(scan)
                db.session.commit()
            raise

        # Fire off a background process
        # TODO: save these into a process-local datastructure, or save
        # it into the DB as well so that we can cull 'processing' tasks
        # that are actually dead.
        process_scan.delay(scan_id=scan.id, scan_type=exam.layout.value)

        return {
            'id': scan.id,
            'name': scan.name,
            'status': scan.status,
            'message': scan.message
        }
