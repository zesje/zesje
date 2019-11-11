""" REST api for graders page """

from flask import abort
from flask_restful import Resource, reqparse

from ..database import db

from ._helpers import required_string
from ..database import Grader
from ..pregrader import AUTOGRADER_NAME


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
            for g in Grader.query.filter(Grader.name != AUTOGRADER_NAME).all()
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

        name = args['name']

        grader = Grader.query.filter(Grader.name == name).one_or_none()

        if grader:
            return dict(status=409, message=f'Grader with name {name} already exists.'), 409

        try:
            db.session.add(Grader(name=name))
            db.session.commit()
        except KeyError as error:
            abort(400, error)

        return self.get()
