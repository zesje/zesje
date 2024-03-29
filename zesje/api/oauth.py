"""REST API for OAuth callback"""

from flask import current_app, session, request, redirect, url_for
from flask.views import MethodView
from flask_login import login_user, current_user, logout_user
from requests_oauthlib import OAuth2Session
from urllib.parse import urlparse
from webargs import fields

from ._helpers import use_kwargs
from ..database import db, Grader


class OAuthStart(MethodView):
    @use_kwargs({"user_url": fields.Str(required=False, load_default=None, data_key="userurl")}, location="query")
    def get(self, user_url):
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
        session["oauth_userurl"] = urlparse(user_url).path if user_url else url_for("index")

        if current_app.config["LOGIN_DISABLED"]:
            authorization_url, state = url_for("zesje.oauth_callback"), "state"
        else:
            oauth2_session = OAuth2Session(
                current_app.config["OAUTH_CLIENT_ID"],
                redirect_uri=url_for("zesje.oauth_callback", _external=True),
                scope=current_app.config["OAUTH_SCOPES"],
            )
            # add prompt='login' below to force surf conext to ask for login everytime disabling single sign-on, see:
            # https://wiki.surfnet.nl/display/surfconextdev/OpenID+Connect+features#OpenIDConnectfeatures-Prompt=login
            authorization_url, state = oauth2_session.authorization_url(current_app.config["OAUTH_AUTHORIZATION_URL"])

        session["oauth_state"] = state

        return redirect(authorization_url)


class OAuthCallback(MethodView):
    def get(self):
        """OAuth provider redirects to this route after authorization. Fetches token and redirects /

        Returns
        -------
        redirect to /
        """
        user_url = session["oauth_userurl"]
        del session["oauth_userurl"]

        if current_app.config["LOGIN_DISABLED"]:
            login_user(Grader.query.first())
            return redirect(user_url)

        oauth2_session = OAuth2Session(
            current_app.config["OAUTH_CLIENT_ID"],
            redirect_uri=url_for("zesje.oauth_callback", _external=True),
            state=session["oauth_state"],
        )

        token = oauth2_session.fetch_token(
            current_app.config["OAUTH_TOKEN_URL"],
            client_secret=current_app.config["OAUTH_CLIENT_SECRET"],
            authorization_response=request.url,
        )

        # token can used to make requests with OAuth provider later if needed
        session["oauth_token"] = token

        oauth_provider = OAuth2Session(current_app.config["OAUTH_CLIENT_ID"], token=token)
        current_login = oauth_provider.get(current_app.config["OAUTH_INFO_URL"]).json()
        oauth_id = current_login[current_app.config["OAUTH_ID_FIELD"]]
        grader = Grader.query.filter(Grader.oauth_id == oauth_id).one_or_none()

        if grader is None or grader.internal:
            # TODO: the app rejects any access to everyone who is not added to the list of allowed graders by the owner
            # In !306 this will change, all new users can be added to the db as they won't have acess to any course
            return redirect(url_for("index") + "unauthorized")
        elif grader.name is None:
            grader.name = current_login[current_app.config["OAUTH_NAME_FIELD"]]
            db.session.commit()

        login_user(grader)

        return redirect(user_url)


class OAuthStatus(MethodView):
    def get(self):
        """returns the current oauth status

        Returns
        -------
        grader: {
            id: str
            name: str
            oauth_id: str
        }
        provider: str
        oauth_id_field:
        """
        if not current_user.is_authenticated:
            return (
                dict(
                    status=401,
                    provider=current_app.config["OAUTH_PROVIDER"],
                ),
                401,
            )

        return dict(
            grader=dict(id=current_user.id, name=current_user.name, oauth_id=current_user.oauth_id),
            provider=current_app.config["OAUTH_PROVIDER"],
            oauth_id_field=current_app.config["OAUTH_ID_FIELD"],
        )


class OAuthLogout(MethodView):
    def get(self):
        """Logs the user out

        Returns
        -------
        status: int
        message: str
        """
        logout_user()
        return dict(status=200, message="Logout successful"), 200
