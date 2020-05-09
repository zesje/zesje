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

# Github OAuth
OAUTH_CLIENT_ID = None
OAUTH_CLIENT_SECRET = None
OAUTH_AUTHORIZATION_BASE_URL = "https://github.com/login/oauth/authorize"
OAUTH_TOKEN_URL = "https://github.com/login/oauth/access_token"
OAUTH_USERINFO_URL = "https://api.github.com/user"
OAUTH_ID_FIELD = "email"
OAUTH_NAME_FIELD = "name"

# Instance owner details
OWNER_OAUTH_ID = 'P.Dixit@student.tudelft.nl'
OWNER_NAME = 'Pradyuman Dixit'

# Routes exempted from authentication
EXEMPTED_ROUTES = ['login', 'callback', 'current_grader']