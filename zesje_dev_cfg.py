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
GITHUB_CLIENT_ID = "011cd525d6cbb9e98687"
GITHUB_CLIENT_SECRET = "5b733b6aa3681ca0e7e3c3d560c84291912e7e01"
GITHUB_AUTHORIZATION_BASE_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USERINFO_URL = "https://api.github.com/user"
