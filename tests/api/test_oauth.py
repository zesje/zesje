import pytest
import requests_mock
from urllib.parse import urlparse, parse_qs

from zesje.database import db, Grader
from zesje.constants import OAUTH_PROVIDERS


@pytest.fixture
def login_app(app):
    app.config['LOGIN_DISABLED'] = False
    yield app
    app.config['LOGIN_DISABLED'] = True


@pytest.fixture
def login_client(login_app):
    with login_app.test_client() as client:
        yield client


@pytest.fixture
def add_grader(login_app):
    db.session.add(Grader(oauth_id='test'))
    db.session.commit()


@pytest.fixture
def callback_request(login_client, login_app):
    result = login_client.get('/api/oauth/start')
    with requests_mock.Mocker() as m:
        m.post(OAUTH_PROVIDERS[login_app.config['OAUTH_PROVIDER']]['TOKEN_URL'],
               json={'access_token': 'test', 'token_type': 'Bearer'})
        m.get(OAUTH_PROVIDERS[login_app.config['OAUTH_PROVIDER']]['USERINFO_URL'],
              json={OAUTH_PROVIDERS[login_app.config['OAUTH_PROVIDER']]['ID_FIELD']: 'test',
                    OAUTH_PROVIDERS[login_app.config['OAUTH_PROVIDER']]['NAME_FIELD']: 'test_name'})
        return login_client.get('/api/oauth/callback?code=test&state=' + result.get_json()['state'])


def test_oauth_start(login_client, login_app):
    result = login_client.get('/api/oauth/start')
    assert result.status_code == 200

    parsed = urlparse(result.get_json()['redirect_oauth'])
    query = parse_qs(parsed.query)
    print(parsed, query)
    assert query['client_id'][0] == OAUTH_PROVIDERS[login_app.config['OAUTH_PROVIDER']]['CLIENT_ID']
    assert query['redirect_uri'][0] == login_app.config['OAUTH_REDIRECT_URI']


def test_oauth_callback_unauthorized_grader(callback_request):
    assert callback_request.headers['Location'].rsplit('/', 1)[1] == 'unauthorized'


def test_oauth_callback_authorized_grader(add_grader, callback_request):
    assert callback_request.status_code == 302


def test_current_grader(login_client, add_grader, callback_request):
    result = login_client.get('/api/oauth/grader')
    assert result.status_code == 200
    assert result.get_json()['oauth_id'] == 'test'


def test_logout(login_client, add_grader, callback_request):
    result = login_client.get('/api/oauth/logout')
    assert result.status_code == 200
    assert login_client.get('/api/oauth/grader').status_code == 401
