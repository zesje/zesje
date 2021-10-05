import pytest
import requests_mock
from urllib.parse import urlparse, parse_qs

from zesje.database import db, Grader


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
    db.session.add(Grader(name=login_app.config['OWNER_NAME'],
                          oauth_id=login_app.config['OWNER_OAUTH_ID']))
    db.session.commit()


@pytest.fixture
def callback_request(login_client, login_app):
    url = login_client.get('/api/oauth/start').location
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    with requests_mock.Mocker() as m:
        m.post(login_app.config['OAUTH_TOKEN_URL'],
               json={'access_token': 'test', 'token_type': 'Bearer'})
        m.get(login_app.config['OAUTH_INFO_URL'],
              json={login_app.config['OAUTH_ID_FIELD']: login_app.config['OWNER_OAUTH_ID'],
                    login_app.config['OAUTH_NAME_FIELD']: login_app.config['OWNER_NAME']})
        return login_client.get('/api/oauth/callback?code=test&state=' + query['state'][0])


def test_oauth_start(login_client, login_app):
    result = login_client.get('/api/oauth/start')
    assert result.status_code == 302

    parsed = urlparse(result.location)
    query = parse_qs(parsed.query)
    assert query['client_id'][0] == login_app.config['OAUTH_CLIENT_ID']
    assert 'redirect_uri' in query and len(query['redirect_uri']) == 1
    assert 'state' in query and len(query['state']) == 1


@pytest.mark.parametrize('url, expected', [
    ('', '/'),
    ('/graders', '/graders'),
    ('http://evil.com/page', '/page')],
    ids=['Empty', 'Normal', 'Malicious'])
def test_oauth_start_userurl(login_client, url, expected):
    login_client.get('/api/oauth/start' + (f'?userurl={url}' if url else ''))

    with login_client.session_transaction() as session:
        assert session['oauth_userurl'] == expected


def test_oauth_callback_unauthorized_grader(callback_request):
    assert callback_request.headers['Location'].rsplit('/', 1)[1] == 'unauthorized'


def test_oauth_callback_authorized_grader(add_grader, callback_request):
    assert callback_request.status_code == 302


def test_current_grader(login_app, login_client, add_grader, callback_request):
    result = login_client.get('/api/oauth/status')
    assert result.status_code == 200
    assert result.get_json()['grader']['oauth_id'] == login_app.config['OWNER_OAUTH_ID']


def test_internal_grader(login_app, login_client):
    db.session.add(Grader(name='internal',
                          oauth_id='grader_123456789',
                          internal=True))
    db.session.commit()

    url = login_client.get('/api/oauth/start').location
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    with requests_mock.Mocker() as m:
        m.post(login_app.config['OAUTH_TOKEN_URL'],
               json={'access_token': 'test', 'token_type': 'Bearer'})
        m.get(login_app.config['OAUTH_INFO_URL'],
              json={login_app.config['OAUTH_ID_FIELD']: 'grader_123456789',
                    login_app.config['OAUTH_NAME_FIELD']: 'something else'})
        am_i_authorised = login_client.get('/api/oauth/callback?code=test&state=' + query['state'][0])

    assert am_i_authorised.headers['Location'].rsplit('/', 1)[1] == 'unauthorized'


def test_logout(login_client, add_grader, callback_request):
    result = login_client.get('/api/oauth/logout')
    assert result.status_code == 200
    assert login_client.get('/api/oauth/status').status_code == 401
