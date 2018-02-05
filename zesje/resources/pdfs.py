import os

from flask import abort, current_app as app
from flask_restful import Resource, reqparse
from werkzeug.datastructures import FileStorage

from pony import orm

from ..models import db, Exam


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
        return self._get(exam_id)

    # Do not call this method without wrapping it in 'orm.db_session'
    def _get(self, exam_id):
        data_dir = app.config['DATA_DIRECTORY']
        exam = Exam[exam_id]

        exam_data_dir = os.path.join(data_dir, f'{exam.name}_data')
        pdfs = [pdf for pdf in os.listdir(exam_data_dir) if pdf.endswith('.pdf')]

        return [{'name': pdf} for pdf in pdfs]


    post_parser = reqparse.RequestParser()
    post_parser.add_argument('pdf', type=FileStorage, required=True,
                             location='files')

    @orm.db_session
    def post(self, exam_id):
        """Upload a PDF

        Parameters
        ----------
        exam_id : int
        pdf : FileStorage
        """
        args = self.post_parser.parse_args()
        # process PDF
