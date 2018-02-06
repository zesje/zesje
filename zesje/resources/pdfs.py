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
        return [
            {
                'id': 1,
                'name': 'hello.pdf',
                'status': 'processing',
                'message': 'extracting images',
            }
        ]

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

        Returns
        -------
        id : int
        name : str
        status : str
        message : str
        """
        args = self.post_parser.parse_args()
        return {
            'id': 1,
            'name': 'hello.pdf',
            'status': 'processing',
            'message': 'going',
        }
