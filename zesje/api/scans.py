import os

from flask import current_app
from flask_restful import Resource, reqparse
from werkzeug.datastructures import FileStorage

from ..scans import process_pdf
from ..raw_scans import process_zipped_images
from ..database import db, Exam, Scan


class Scans(Resource):
    """Getting a list of uploaded scans, and uploading new ones."""

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

        exam = Exam.query.get(exam_id)
        if exam is None:
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
    post_parser.add_argument('pdf', type=FileStorage, required=True,
                             location='files')

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
        if args['pdf'].mimetype != 'application/pdf':
            return dict(message='Uploaded file is not a PDF'), 400

        exam = Exam.query.get(exam_id)
        if exam is None:
            return dict(status=404, message='Exam does not exist.'), 404
        elif not exam.finalized:
            return dict(status=403, message='Exam is not finalized.'), 403

        scan = Scan(exam=exam, name=args['pdf'].filename,
                    status='processing', message='Waiting...')
        db.session.add(scan)
        db.session.commit()

        try:
            path = os.path.join(current_app.config['SCAN_DIRECTORY'], f'{scan.id}.pdf')
            args['pdf'].save(path)
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
        process_pdf.delay(scan_id=scan.id)

        return {
            'id': scan.id,
            'name': scan.name,
            'status': scan.status,
            'message': scan.message
        }


class ZippedScan(Resource):

    post_parser = reqparse.RequestParser()
    post_parser.add_argument('file', type=FileStorage, required=True,
                             location='files')

    def post(self, exam_id):
        """Upload a zip with images

        Parameters
        ----------
        exam_id : int
        file : FileStorage

        Returns
        -------
        id : int
        name : str
        status : str
        message : str
        """
        args = self.post_parser.parse_args()
        if args['file'].mimetype != 'application/zip':
            return dict(message='Uploaded file is not a ZIP'), 400

        exam = Exam.query.get(exam_id)
        if exam is None:
            return dict(status=404, message='Exam does not exist.'), 404
        elif not exam.finalized:
            return dict(status=403, message='Exam is not finalized.'), 403

        scan = Scan(exam=exam, name=args['file'].filename,
                    status='processing', message='Waiting...')
        db.session.add(scan)
        db.session.commit()

        try:
            path = os.path.join(current_app.config['SCAN_DIRECTORY'], f'{scan.id}.zip')
            args['file'].save(path)
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
        process_zipped_images.delay(scan_id=scan.id)

        return {
            'id': scan.id,
            'name': scan.name,
            'status': scan.status,
            'message': scan.message
        }
