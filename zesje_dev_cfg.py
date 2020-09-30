import os
# Folder to save exam scans and database
DATA_DIRECTORY = 'data-dev'

# Root password to set at database initialization
MYSQL_ROOT_PASSWORD = 'rootpsw'

# Email settings
USE_SSL = False
SMTP_SERVER = 'dutmail.tudelft.nl'
SMTP_PORT = '25'
FROM_ADDRESS = 'noreply@tudelft.nl'
SMTP_USERNAME = ''
SMTP_PASSWORD = ''

LOGIN_DISABLED = True

# Enable debug mode
DEBUG = 1

# Secret key required for flask.session
SECRET_KEY = os.urandom(25)

# OAuth Details
OAUTH_CLIENT_ID = 'dev'
OAUTH_CLIENT_SECRET = 'dev_secret'
OAUTH_AUTHORIZATION_BASE_URL = 'https://connect.test.surfconext.nl/oidc/authorize'
OAUTH_TOKEN_URL = 'https://connect.test.surfconext.nl/oidc/token'
OAUTH_USERINFO_URL = 'https://connect.test.surfconext.nl/oidc/userinfo'
OAUTH_ID_FIELD = "email"
OAUTH_NAME_FIELD = "name"
OAUTH_PROVIDER = 'Surf Context'
OAUTH_SCOPES = ['openid']
OAUTH_INSECURE_TRANSPORT = True

# Instance owner details
OWNER_OAUTH_ID = 'admin@admin'
OWNER_NAME = 'admin'
