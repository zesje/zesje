""" REST api for graders page """

from flask import abort
from flask_restful import Resource, reqparse

from ..database import db

from ._helpers import required_string
from ..database import Grader


# TODO: when making new database structure, have only a single
#       'name' field: it is just an identifier

class Graders(Resource):
    """ Graders that are able to use the software, also logged during grading """

    def get(self):
        """get all graders.

        Returns
        -------
        list of:
            id: int
            name: str
        """
        return [
            {
                'id': g.id,
                'name': g.name
            }
            for g in Grader.query.all()
        ]

    post_parser = reqparse.RequestParser()
    required_string(post_parser, 'name')

    def post(self):
        """add a grader.

        Parameters
        ----------
        name: str

        Returns
        -------
        list of:
            id: int
            name: str
        """
        args = self.post_parser.parse_args()

        try:
            db.session.add(Grader(name=args['name']))
            db.session.commit()
        except KeyError as error:
            abort(400, error)

        return self.get()
