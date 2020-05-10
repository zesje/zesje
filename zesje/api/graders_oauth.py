""" REST api for graders page """

from flask_restful import Resource
from flask_login import current_user


class GradersOAuth(Resource):
    def get(self):
        # returns details of the current grader logged in
        return dict(
            id=current_user.id,
            name=current_user.name,
            oauth_id=current_user.oauth_id
        )
