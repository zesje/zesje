""" REST api for initiating OAuth connection """

from flask_restful import Resource
from flask import current_app, session
from requests_oauthlib import OAuth2Session
from flask_login import current_user


class OAuthInitiate(Resource):
    def get(self):
        """Logs the user in by redirecting to the OAuth provider with the appropriate
                client ID as a request parameter"""
        oauth2_session = OAuth2Session(current_app.config['OAUTH_CLIENT_ID'])
        authorization_url, state = oauth2_session.authorization_url(current_app.config['OAUTH_AUTHORIZATION_BASE_URL'])

        session['oauth_state'] = state

        is_authenticated = (current_user is not None) and current_user.is_authenticated

        return {
            'redirect_oauth': authorization_url,
            'provider': current_app.config['OAUTH_PROVIDER'],
            'state': state,
            'is_authenticated': is_authenticated
        }
