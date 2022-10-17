import redis

# Folder to save exam scans and database
DATA_DIRECTORY = 'data'

# Page size supported by the printers one of 'A4' or "US letter"
PAGE_FORMAT = 'A4'

# Email settings (not configured by default)
USE_SSL = None
SMTP_SERVER = None
SMTP_PORT = None
FROM_ADDRESS = None
SMTP_USERNAME = None
SMTP_PASSWORD = None

# MySQL host
MYSQL_USER = 'zesje'
MYSQL_PASSWORD = 'zesjepsw'
MYSQL_HOST = 'localhost'
MYSQL_DATABASE = 'course'
MYSQL_CONNECTOR = 'mysql+pymysql'

CELERY_BROKER_URL = 'redis://localhost:6479'
CELERY_RESULT_BACKEND = 'redis://localhost:6479'

# Number of proxies Zesje is behind, needed to handle headers correctly
# Only affects the wsgi app in zesje/wsgi.py
PROXY_COUNT = 1

LOGIN_DISABLED = False

# Secret key required for flask.session
SECRET_KEY = None
SESSION_TYPE = 'redis'
SESSION_REDIS = redis.Redis(port=6479)

# Prevent CSRF
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_SAMESITE = 'Lax'

# Instance owner details
OWNER_OAUTH_ID = None
OWNER_NAME = None

# OAuth configuration
OAUTH_INSECURE_TRANSPORT = False

# OAuth GitLab provider
OAUTH_CLIENT_ID = ''
OAUTH_CLIENT_SECRET = ''
OAUTH_AUTHORIZATION_URL = 'https://gitlab.kwant-project.org/oauth/authorize'
OAUTH_TOKEN_URL = 'https://gitlab.kwant-project.org/oauth/token'
OAUTH_INFO_URL = 'https://gitlab.kwant-project.org/oauth/userinfo'
OAUTH_ID_FIELD = 'email'
OAUTH_NAME_FIELD = 'name'
OAUTH_PROVIDER = 'GitLab'
OAUTH_SCOPES = ['openid', 'email']

# OAuth TU Delft provider
# OAUTH_CLIENT_ID = ''
# OAUTH_CLIENT_SECRET = ''
# OAUTH_AUTHORIZATION_URL = 'https://connect.test.surfconext.nl/oidc/authorize'
# OAUTH_TOKEN_URL = 'https://connect.test.surfconext.nl/oidc/token'
# OAUTH_INFO_URL = 'https://connect.test.surfconext.nl/oidc/userinfo'
# OAUTH_ID_FIELD = 'email'
# OAUTH_NAME_FIELD = 'name'
# OAUTH_PROVIDER = 'Surf Conext'
# OAUTH_SCOPES = ['openid']
