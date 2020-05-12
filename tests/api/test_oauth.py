# Actual tests
from zesje.database import db, Grader
import pytest
import requests_mock


@pytest.fixture
def add_grader(app):
    db.session.add(Grader(oauth_id='test'))
    db.session.commit()


@pytest.fixture
def callback_request(test_client, config_app):
    result = test_client.get('/api/oauth/start')
    with requests_mock.Mocker() as m:
        m.post(config_app.config['OAUTH_TOKEN_URL'], json={'access_token': 'test', 'token_type': 'Bearer'})
        m.get(config_app.config['OAUTH_USERINFO_URL'], json={config_app.config['OAUTH_ID_FIELD']: 'test',
                                                             config_app.config['OAUTH_NAME_FIELD']: 'test_name'})
        return test_client.get('/api/oauth/callback?code=test&state=' + result.get_json()['state'])


def test_oauth_start(test_client, config_app):
    result = test_client.get('/api/oauth/start')
    assert result.status_code == 200
    assert result.get_json()['redirect_oauth'] == \
        config_app.config['OAUTH_AUTHORIZATION_BASE_URL'] + '?response_type=code&client_id=' + \
        config_app.config['OAUTH_CLIENT_ID'] + '&state=' + result.get_json()['state']


def test_oauth_callback_unauthorized_grader(callback_request):
    assert callback_request.status_code == 403


def test_oauth_callback_authorized_grader(add_grader, callback_request):
    assert callback_request.status_code == 302


def test_current_grader(test_client, add_grader, callback_request):
    result = test_client.get('/api/oauth/grader')
    assert result.status_code == 200
    assert result.get_json()['oauth_id'] == 'test'


def test_logout(test_client, add_grader, callback_request):
    result = test_client.get('/api/oauth/logout')
    assert result.status_code == 200
    assert test_client.get('/api/oauth/grader').status_code == 401
