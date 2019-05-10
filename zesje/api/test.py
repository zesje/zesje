
from flask_restful import Resource


class Test(Resource):
    """
    Class used to make test api calls
    """
    def get(self):
        # Call your code here, and edit the message to return specific objects

        return dict(message='ok', code=200), 200
