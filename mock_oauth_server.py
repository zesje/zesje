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
    parsed_url = urlparse(request.url)
    query_params = parse_qs(parsed_url.query)
    return redirect(
        f"{app.config['OAUTH_REDIRECT_URI']}?code=test&state={query_params['state'][0]}"
    )


@app.route('/user', methods=['GET'])
def user():
    return dict(
        email=app.config['OWNER_OAUTH_ID'],
        name=app.config['OWNER_NAME']
    )


@app.route('/token', methods=['POST'])
def token():
    return dict(
        access_token='token',
        token_type='bearer'
    )


if __name__ == '__main__':
    app.run(debug=True, port='8080')
