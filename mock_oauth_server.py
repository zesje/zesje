import os
from urllib.parse import urlparse, parse_qs

from flask import Flask, request, redirect

app = Flask(__name__)


if 'ZESJE_SETTINGS' in os.environ:
    app.config.from_envvar('ZESJE_SETTINGS')
else:
    app.config.from_object('zesje_default_cfg')
    app.config.from_object('zesje_dev_cfg')


@app.route('/authorize', methods=['GET'])
def authorize():
    """Authorises the user and redirects to the desired location."""
    parsed_url = urlparse(request.url)
    query_params = parse_qs(parsed_url.query)
    return redirect(
        f"{query_params['redirect_uri'][0]}?code=test&state={query_params['state'][0]}"
    )


@app.route('/user', methods=['GET'])
def user():
    """Returns user information"""
    return dict(
        email=app.config['OWNER_OAUTH_ID'],
        name=app.config['OWNER_NAME']
    )


@app.route('/token', methods=['POST'])
def token():
    """Returns the Oauth2 token to be used"""
    return dict(
        access_token='token',
        token_type='bearer'
    )


if __name__ == '__main__':
    app.run(debug=True, port='8080')
