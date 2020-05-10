"""REST API for OAuth callback"""

from flask_restful import Resource
from flask import current_app, session, request, redirect, url_for
from flask_login import login_user
from requests_oauthlib import OAuth2Session

from ..database import Grader


class OAuthCallback(Resource):
    def get(self):
        """OAuth provider redirects to this route after authorization.
                Fetches token and redirects to /profile"""
        oauth2_session = OAuth2Session(current_app.config['OAUTH_CLIENT_ID'], state=session['oauth_state'])
        token = oauth2_session.fetch_token(
          current_app.config['OAUTH_TOKEN_URL'],
          client_secret=current_app.config['OAUTH_CLIENT_SECRET'],
          authorization_response=request.url,
        )

        session['oauth_token'] = token  # token can used to make requests with OAuth provider later if needed

        github = OAuth2Session(current_app.config['OAUTH_CLIENT_ID'], token=session['oauth_token'])
        current_login = github.get(current_app.config['OAUTH_USERINFO_URL']).json()

        grader = Grader.query.filter(Grader.oauth_id ==
                                     current_login[current_app.config['OAUTH_ID_FIELD']]).one_or_none()

        if grader is None:
            return "Your account is Unauthorized. Please contact somebody who has access"
        elif grader.name is None:
            grader.name = current_login[current_app.config['OAUTH_NAME_FIELD']]

        login_user(grader)

        return redirect(url_for('index'))
