"""Rest API for getting the grader of the current session"""

from flask import session
from flask_restful import Resource

from ..database import Grader


class CurrentGrader(Resource):
    """Gets the current grader who logged in via OAuth"""

    def get(self):
        """get the name of the current grader

        Returns
        -------
        id : int
        name : str
        """

        grader = Grader.query.filter(Grader.id == session['grader_id'])

        return {
            'id': grader.id,
            'name': grader.name,
            'oauth_id': grader.oauth_id
        }
