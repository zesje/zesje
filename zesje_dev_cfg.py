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

# Enable debug mode
DEBUG = 1

# Secret key required for flask.session
SECRET_KEY = os.urandom(25)

# OAuth Details
OAUTH_CLIENT_ID = None
OAUTH_CLIENT_SECRET = None
OAUTH_AUTHORIZATION_BASE_URL = None
OAUTH_TOKEN_URL = None
OAUTH_USERINFO_URL = None
OAUTH_ID_FIELD = "email"
OAUTH_NAME_FIELD = "name"
OAUTH_PROVIDER = None
INSECURE_TRANSPORT = '1'

# Instance owner details
OWNER_OAUTH_ID = None
OWNER_NAME = None

# Routes exempted from authentication
EXEMPTED_ROUTES = ['zesje.api.oauthinitiate', 'zesje.api.oauthcallback', 'index']
