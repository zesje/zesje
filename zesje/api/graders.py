""" REST api for graders page """

from flask import abort
from flask_restful import Resource, reqparse

from pony import orm

from ._helpers import required_string
from ..models import Grader


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
            first_name: str
            last_name: str
        """
        return self._get()

    @orm.db_session
    def _get(self):
        return [
            {
                'id': g.id,
                'first_name': g.first_name,
                'last_name': g.last_name
            }
            for g in Grader.select()
        ]

    post_parser = reqparse.RequestParser()
    required_string(post_parser, 'first_name')
    required_string(post_parser, 'last_name')

    @orm.db_session
    def post(self):
        """add a grader.

        Parameters
        ----------
        first_name: str
        last_name: str

        Returns
        -------
        list of:
            id: int
            first_name: str
            last_name: str
        """
        args = self.post_parser.parse_args()

        try:
            Grader(first_name=args['first_name'], last_name=args['last_name'])
            orm.commit()
        except KeyError as error:
            abort(400, error)

        return self._get()
