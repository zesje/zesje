"""REST API for OAuth callback"""

from flask_restful import Resource
from flask import current_app, session, request, redirect, url_for
from flask_login import login_user, current_user, logout_user
from requests_oauthlib import OAuth2Session

from ..database import db, Grader


class OAuthStart(Resource):
    def get(self):
        """Logs the user in by redirecting to the OAuth provider with the appropriate client ID

        Returns
        -------
        redirect_oauth: str
         the external URL of the OAuth2 provider to redirect to
        provider: str
         the name of the OAuth2 provider
        state: str
         returns current state, used for testing
        is_authenticated: boolean
        """
        if current_app.config['LOGIN_DISABLED']:
            authorization_url, state = url_for('zesje.oauthcallback'), 'state'
        else:
            oauth2_session = OAuth2Session(current_app.config['OAUTH_CLIENT_ID'],
                                           redirect_uri=url_for('zesje.oauthcallback', _external=True),
                                           scope=current_app.config['OAUTH_SCOPES'])
            # add prompt='login' below to force surf conext to ask for login everytime disabling single sign-on, see:
            # https://wiki.surfnet.nl/display/surfconextdev/OpenID+Connect+features#OpenIDConnectfeatures-Prompt=login
            authorization_url, state = oauth2_session\
                .authorization_url(current_app.config['OAUTH_AUTHORIZATION_URL'])

        session['oauth_state'] = state

        return {
            'redirect_oauth': authorization_url,
            'provider': current_app.config['OAUTH_PROVIDER'],
            'state': state,
            'is_authenticated': current_user.is_authenticated,
            'oauth_id_field': current_app.config['OAUTH_ID_FIELD']
        }


class OAuthCallback(Resource):
    def get(self):
        """OAuth provider redirects to this route after authorization. Fetches token and redirects /

        Returns
        -------
        redirect to /
        """
        if current_app.config['LOGIN_DISABLED']:
            login_user(Grader.query.first())
            return redirect(url_for('index'))

        oauth2_session = OAuth2Session(current_app.config['OAUTH_CLIENT_ID'],
                                       redirect_uri=url_for('zesje.oauthcallback', _external=True),
                                       state=session['oauth_state'])

        token = oauth2_session.fetch_token(
            current_app.config['OAUTH_TOKEN_URL'],
            client_secret=current_app.config['OAUTH_CLIENT_SECRET'],
            authorization_response=request.url,
        )

        # token can used to make requests with OAuth provider later if needed
        session['oauth_token'] = token

        oauth_provider = OAuth2Session(current_app.config['OAUTH_CLIENT_ID'], token=token)
        current_login = oauth_provider.get(current_app.config['OAUTH_INFO_URL']).json()
        oauth_id = current_login[current_app.config['OAUTH_ID_FIELD']]
        grader = Grader.query.filter(Grader.oauth_id == oauth_id).one_or_none()

        if grader is None or grader.internal:
            # TODO: the app rejects any access to everyone who is not added to the list of allowed graders by the owner
            # In !306 this will change, all new users can be added to the db as they won't have acess to any course
            return redirect(url_for('index') + 'unauthorized')
        elif grader.name is None:
            grader.name = current_login[current_app.config['OAUTH_NAME_FIELD']]
            db.session.commit()

        login_user(grader)

        return redirect(url_for('index'))


class OAuthGrader(Resource):
    def get(self):
        """returns details of the current grader logged in

        Returns
        -------
        id: str
        name: str
        oauth_id: str
        """
        if not current_user.is_authenticated:
            return dict(status=401, message="Not logged in"), 401

        return dict(
            id=current_user.id,
            name=current_user.name,
            oauth_id=current_user.oauth_id
        )


class OAuthLogout(Resource):
    def get(self):
        """Logs the user out

        Returns
        -------
        status: int
        message: str
        """
        logout_user()
        return dict(status=200, message="Logout successful")
