"""Rest API for getting the grader of the current session"""

from flask import session
from flask_restful import Resource


class Current_Grader(Resource):
    """Gets the current grader who logged in via OAuth"""

    def get(self):
        """get the name of the current grader

        Returns
        -------
        name : str
        """
        return {
            'name': session['grader_name']
        }
