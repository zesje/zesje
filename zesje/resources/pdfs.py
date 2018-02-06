import os
from multiprocessing import Process

from flask import abort, current_app as app
from flask_restful import Resource, reqparse
from werkzeug.datastructures import FileStorage

from pony import orm

from ..models import db, Exam, PDF
from ..helpers import pdf_helper

class Pdfs(Resource):
    """Getting a list of uploaded PDFs, and uploading new ones."""

    @orm.db_session
    def get(self, exam_id):
        """get all uploaded PDFs for a particular exam.

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
                'id': pdf.id,
                'name': pdf.name,
                'status': pdf.status,
                'message': pdf.message,
            }
            for pdf in PDF.select(lambda pdf: pdf.exam.id == exam_id)
        ]

    post_parser = reqparse.RequestParser()
    post_parser.add_argument('pdf', type=FileStorage, required=True,
                             location='files')

    def post(self, exam_id):
        """Upload a PDF

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
            pdf = PDF(exam=Exam[exam_id], name=args['pdf'].filename,
                      status='processing', message='importing PDF')

        with orm.db_session:
            try:
                path = os.path.join(app.config['PDF_DIRECTORY'], f'{pdf.id}.pdf')
                args['pdf'].save(path)
            except Exception:
                pdf.delete()
                raise

        # Fire off background process
        # TODO: save these into a process-local datastructure, or save
        # it into the DB as well so that we can cull 'processing' tasks
        # that are actually dead.
        Process(target=pdf_helper.process_pdf, args=(pdf.id,)).start()

        return {
            'id': pdf.id,
            'name': pdf.name,
            'status': pdf.status,
            'message': pdf.message
        }
