from flask import current_app
from flask_restful import Resource, reqparse
from werkzeug.datastructures import FileStorage

from ..scans import process_scan
from ..database import db, Exam, Scan


class Scans(Resource):
    """Getting a list of uploaded scans, and uploading new ones."""

    def _is_mimetype_allowed(self, mimetype):
        return (
            mimetype == 'application/pdf' or
            mimetype.startswith('image') or
            mimetype in current_app.config['ZIP_MIME_TYPES']
        )

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

        if (exam := Exam.query.get(exam_id)) is None:
            return dict(status=404, message='Exam does not exist.'), 404

        return [
            {
                'id': scan.id,
                'name': scan.name,
                'status': scan.status,
                'message': scan.message,
            }
            for scan in exam.scans
        ]

    post_parser = reqparse.RequestParser()
    post_parser.add_argument('file', type=FileStorage, required=True,
                             location='files')
    post_parser.add_argument('scan_type', type=str, choices=['normal', 'raw'], required=True)

    def post(self, exam_id):
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
        args = self.post_parser.parse_args()
        if not self._is_mimetype_allowed(args['file'].mimetype):
            return dict(message='File is not a PDF, ZIP or image.'), 400

        if (exam := Exam.query.get(exam_id)) is None:
            return dict(status=404, message='Exam does not exist.'), 404
        elif not exam.finalized:
            return dict(status=403, message='Exam is not finalized.'), 403

        scan = Scan(exam=exam, name=args['file'].filename,
                    status='processing', message='Waiting...')
        db.session.add(scan)
        db.session.commit()

        try:
            args['file'].save(scan.path)
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
        process_scan.delay(scan_id=scan.id, scan_type=args['scan_type'])

        return {
            'id': scan.id,
            'name': scan.name,
            'status': scan.status,
            'message': scan.message
        }
