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
OAUTH_REDIRECT_URI = ''
OAUTH_INSECURE_TRANSPORT = False

# Routes exempted from authentication
EXEMPT_ROUTES = ['zesje.api.oauthstart', 'zesje.api.oauthcallback']
EXEMPT_METHODS = ['OPTIONS']

# Instance owner details
OWNER_OAUTH_ID = None
OWNER_NAME = None
