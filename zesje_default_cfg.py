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

# Secret key required for flask.session
SECRET_KEY = None

# Github OAuth
OAUTH_CLIENT_ID = None
OAUTH_CLIENT_SECRET = None
OAUTH_AUTHORIZATION_BASE_URL = "https://github.com/login/oauth/authorize"
OAUTH_TOKEN_URL = "https://github.com/login/oauth/access_token"
OAUTH_USERINFO_URL = "https://api.github.com/user"
OAUTH_ID_FIELD = "email"
OAUTH_NAME_FIELD = "name"

# Instance owner details
OWNER_OAUTH_ID = None
OWNER_NAME = None

# Routes exempted from authentication
EXEMPTED_ROUTES = ['login', 'callback', 'index']
