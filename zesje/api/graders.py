""" REST api for graders page """

from flask import abort, current_app
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
                'name': g.oauth_id
            }
            for g in Grader.query.filter(Grader.oauth_id != current_app.config['AUTOGRADER_NAME']).all()
        ]

    post_parser = reqparse.RequestParser()
    required_string(post_parser, 'oauth_id')

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

        oauth_id = args['oauth_id']

        grader = Grader.query.filter(Grader.oauth_id == oauth_id).one_or_none()

        if grader:
            return dict(status=409, message=f'Grader with name {oauth_id} already exists.'), 409

        try:
            db.session.add(Grader(oauth_id=oauth_id))
            db.session.commit()
        except KeyError as error:
            abort(400, error)

        return self.get()
