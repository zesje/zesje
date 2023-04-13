MYSQL_DATABASE = "course_test"

SECRET_KEY = "test_secret_key"
SESSION_TYPE = "null"

PROXY_COUNT = 0

LOGIN_DISABLED = True

# Allow cookies over http during testing
SESSION_COOKIE_SECURE = False

OWNER_OAUTH_ID = "test@test"
OWNER_NAME = "test"

# OAuth Details
OAUTHLIB_INSECURE_TRANSPORT = True
OAUTH_PROVIDER = "Mock Server"
OAUTH_CLIENT_ID = "test"
OAUTH_CLIENT_SECRET = "test_secret"
OAUTH_AUTHORIZATION_URL = "https://localhost/oauth/start"
OAUTH_TOKEN_URL = "https://localhost/oauth/token"
OAUTH_INFO_URL = "https://localhost/oauth/userinfo"
OAUTH_ID_FIELD = "email"
OAUTH_NAME_FIELD = "name"
OAUTH_SCOPES = []

# Email settings
USE_SSL = False
SMTP_SERVER = "localhost"
SMTP_PORT = 415
FROM_ADDRESS = "mock@email.nl"
SMTP_USERNAME = ""
SMTP_PASSWORD = ""
