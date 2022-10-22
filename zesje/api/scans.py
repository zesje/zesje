from flask import current_app
from flask.views import MethodView
from webargs import fields

from ._helpers import DBModel, use_kwargs
from ..scans import process_scan
from ..database import db, Exam, Scan


class Scans(MethodView):
    """Getting a list of uploaded scans, and uploading new ones."""

    def _is_mimetype_allowed(self, mimetype):
        return (
            mimetype == 'application/pdf' or
            mimetype.startswith('image') or
            mimetype in current_app.config['ZIP_MIME_TYPES']
        )

    @use_kwargs({'exam_id': DBModel(Exam, required=True)}, location='view_args')
    def get(self, exam_id):
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
            for scan in exam_id.scans
        ]

    @use_kwargs({
        'exam_id': DBModel(Exam, required=True, validate_model=[lambda exam: exam.finalized])
    }, location='view_args')
    @use_kwargs({'file': fields.Field(required=True)}, location='files')
    def post(self, exam_id, file):
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
        if not self._is_mimetype_allowed(file.mimetype):
            return dict(message='File is not a PDF, ZIP or image.'), 400

        scan = Scan(exam=exam_id, name=file.filename,
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
        process_scan.delay(scan_id=scan.id, scan_type=exam_id.layout.value)

        return {
            'id': scan.id,
            'name': scan.name,
            'status': scan.status,
            'message': scan.message
        }
