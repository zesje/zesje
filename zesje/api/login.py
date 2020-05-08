""" REST api for login page """

from flask_restful import Resource


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
