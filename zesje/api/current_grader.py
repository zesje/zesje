"""Rest API for getting the grader of the current session"""

from flask_restful import Resource
from flask_login import current_user


class CurrentGrader(Resource):
    """Gets the current grader who logged in via OAuth"""

    def get(self):
        """get the name of the current grader

        Returns
        -------
        id : int
        name : str
        """

        return {
            'id': current_user.id,
            'name': current_user.name,
            'oauth_id': current_user.oauth_id
        }
