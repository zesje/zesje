""" REST api for graders page """

from flask import abort
from flask_restful import Resource, reqparse

from pony import orm

from ._helpers import required_string
from ..database import Grader


# TODO: when making new database structure, have only a single
#       'name' field: it is just an identifier

class Graders(Resource):
    """ Graders that are able to use the software, also logged during grading """

    @orm.db_session
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
            for g in Grader.select()
        ]

    post_parser = reqparse.RequestParser()
    required_string(post_parser, 'name')

    @orm.db_session
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
            Grader(name=args['name'])
            orm.commit()
        except KeyError as error:
            abort(400, error)

        return self.get()
