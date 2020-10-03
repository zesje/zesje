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
OAUTH_PROVIDER = 'gitlab'
OAUTH_REDIRECT_URI = 'http://127.0.0.1:8881/api/oauth/callback'
OAUTH_INSECURE_TRANSPORT = True

# Instance owner details
OWNER_OAUTH_ID = 'admin@admin'
OWNER_NAME = 'admin'
