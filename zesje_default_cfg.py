# Folder to save exam scans and database
DATA_DIRECTORY = 'data'

# Page size supported by the printers, one of 'A4' or "US letter"
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

CELERY_BROKER_URL = 'redis://localhost:6479',
CELERY_RESULT_BACKEND = 'redis://localhost:6479'

LOGIN_DISABLED = False

# Secret key required for flask.session
SECRET_KEY = None

# OAuth Details
OAUTH_CLIENT_ID = None
OAUTH_CLIENT_SECRET = None
OAUTH_AUTHORIZATION_BASE_URL = None
OAUTH_TOKEN_URL = None
OAUTH_USERINFO_URL = None
OAUTH_ID_FIELD = None
OAUTH_NAME_FIELD = None
OAUTH_PROVIDER = None
OAUTH_REDIRECT_URI = 'http://127.0.0.1:8881/api/oauth/callback'
OAUTH_SCOPES = ['read_user']
OAUTH_INSECURE_TRANSPORT = False

# Routes exempted from authentication
EXEMPT_ROUTES = ['zesje.api.oauthstart', 'zesje.api.oauthcallback']
EXEMPT_METHODS = ['OPTIONS']

# Instance owner details
OWNER_OAUTH_ID = None
OWNER_NAME = None
