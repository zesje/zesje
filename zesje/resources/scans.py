import os
from subprocess import run
import multiprocessing

from flask import abort, current_app as app
from flask_restful import Resource, reqparse
from werkzeug.datastructures import FileStorage

from pony import orm

from ..models import Exam, Scan
from ..helpers import scan_helper

class Scans(Resource):
    """Getting a list of uploaded scans, and uploading new ones."""

    @orm.db_session
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
            for scan in Scan.select(lambda scan: scan.exam.id == exam_id)
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

        with orm.db_session:
            scan = Scan(exam=Exam[exam_id], name=args['pdf'].filename,
                      status='processing', message='importing PDF')

        try:
            path = os.path.join(app.config['SCAN_DIRECTORY'], f'{scan.id}.pdf')
            args['pdf'].save(path)
        except Exception:
            with orm.db_session:
                scan = Scan[scan.id]
                scan.delete()
            raise

        # Fire off a background process
        # TODO: save these into a process-local datastructure, or save
        # it into the DB as well so that we can cull 'processing' tasks
        # that are actually dead.

        # Because sharing a database connection with a subprocess is dangerous,
        # we use the slower "spawn" method that fires up a new process instead
        # of forking.
        args = (scan.id, app.config)
        ctx = multiprocessing.get_context('spawn')
        ctx.Process(target=scan_helper.process_pdf, args=args).start()

        return {
            'id': scan.id,
            'name': scan.name,
            'status': scan.status,
            'message': scan.message
        }
