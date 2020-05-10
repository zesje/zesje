""" REST API for logging out a user"""
from flask_restful import Resource
from flask_login import logout_user


class Logout(Resource):
    def get(self):
        """Logs the user out
                """
        logout_user()
        return dict(status=400, message="Logout successful")