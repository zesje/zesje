# Actual tests


def test_oauth_start(test_client, config_app):
    result = test_client.get('/api/oauth/start')
    assert result.status_code == 200
    assert result.get_json()['redirect_oauth'] == \
        config_app.config['OAUTH_AUTHORIZATION_BASE_URL'] + '?response_type=code&client_id=' + \
        config_app.config['OAUTH_CLIENT_ID'] + '&state=' + result.get_json()['state']
