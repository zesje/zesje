""" REST api for graders page """

from flask import current_app
from flask.views import MethodView
from webargs import fields

from ._helpers import use_kwargs, non_empty_string
from ..database import db, Grader


# TODO: when making new database structure, have only a single
#       'name' field: it is just an identifier
class Graders(MethodView):
    """ Graders that are able to use the software, also logged during grading """

    def get(self):
        """get all graders.

        Returns
        -------
        list of:
            id: int
            oauth_id: str
        """
        return [
            {
                'id': g.id,
                'oauth_id': g.oauth_id,
                'name': g.name
            }
            for g in Grader.query.filter(Grader.oauth_id != current_app.config['AUTOGRADER_NAME']).all()
        ]

    @use_kwargs({"oauth_id": fields.Email(required=True, validate=non_empty_string)}, location='json')
    def post(self, oauth_id):
        """add a grader.

        Parameters
        ----------
        oauth_id: str

        Returns
        -------
        list of:
            id: int
            name: str
        """
        oauth_id = oauth_id.strip()
        if Grader.query.filter(Grader.oauth_id == oauth_id).one_or_none():
            return dict(status=409, message=f'Grader with id {oauth_id} already exists.'), 409

        try:
            db.session.add(Grader(oauth_id=oauth_id))
            db.session.commit()
        except KeyError as error:
            return dict(status=400, message=str(error)), 400

        return self.get()
