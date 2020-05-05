""" REST api for login page """

from flask import abort, current_app
from flask_restful import Resource, reqparse

from ..database import db

from ._helpers import required_string
from ..database import Grader


# TODO: when making new database structure, have only a single
#       'name' field: it is just an identifier

class Login(Resource):
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
            "awesome"
        ]

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
