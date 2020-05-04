import os
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

#Secret key required for flask.session
SECRET_KEY = os.urandom(25)

#Github OAuth
GITHUB_CLIENT_ID = "011cd525d6cbb9e98687"
GITHUB_CLIENT_SECRET = "5b733b6aa3681ca0e7e3c3d560c84291912e7e01"
GITHUB_AUTHORIZATION_BASE_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USERINFO_URL = "https://api.github.com/user"