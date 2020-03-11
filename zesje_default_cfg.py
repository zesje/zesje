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

CELERY_BROKER_URL = 'redis://localhost:6479',
CELERY_RESULT_BACKEND = 'redis://localhost:6479'
