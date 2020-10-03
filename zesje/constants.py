from reportlab.lib.units import mm

# student id widget
ID_GRID_FONT_SIZE = 11  # Size of font
ID_GRID_FONT = 'Helvetica'
ID_GRID_MARGIN = 5  # Margin between elements and sides
ID_GRID_DIGITS = 7  # Max amount of digits you want for student numbers
ID_GRID_BOX_SIZE = ID_GRID_FONT_SIZE - 2  # Size of student number boxes
ID_GRID_TEXT_BOX_SIZE = (ID_GRID_FONT_SIZE * 15, ID_GRID_BOX_SIZE * 2 + ID_GRID_MARGIN + 2)  # size of textbox

# copy number widget
COPY_NUMBER_MATRIX_BOX_SIZE = 44
COPY_NUMBER_FONTSIZE = 12  # Size of font
COPY_NUMBER_FONT = 'Helvetica'

# format used for generated copy pdf's
OUTPUT_PDF_FILENAME_FORMAT = '{0:05d}.pdf'

# the size of the markers in points
MARKER_MARGIN = 10 * mm
MARKER_LINE_LENGTH = 8 * mm
MARKER_LINE_WIDTH = 1

# the parameters of drawing checkboxes
CHECKBOX_MARGIN = 5
CHECKBOX_FONT_SIZE = 11
CHECKBOX_FONT = 'Helvetica'
CHECKBOX_SIZE = 9

PAGE_FORMATS = {
    "A4": (595.276, 841.89),
    "US letter": (612, 792),
}

AUTOGRADER_NAME = 'Zesje'
BLANK_FEEDBACK_NAME = 'Blank'

# Allow up to 1 mm misalignment in any direction
MAX_ALIGNMENT_ERROR_MM = 1

# Make sure a roughly 1 cm long line written with
# a ballpoint pen is regarded as not blank.
MIN_ANSWER_SIZE_MM2 = 4

SQLALCHEMY_TRACK_MODIFICATIONS = False  # Suppress future deprecation warning

ZIP_MIME_TYPES = ['application/zip', 'application/octet-stream', 'application/x-zip-compressed', 'multipart/x-zip']

OAUTH_PROVIDERS = {
    'gitlab': {
        'AUTHORIZATION_BASE_URL': 'https://gitlab.kwant-project.org/oauth/authorize',
        'TOKEN_URL': 'https://gitlab.kwant-project.org/oauth/token',
        'USERINFO_URL': 'https://gitlab.kwant-project.org/api/v4/user',
        'ID_FIELD': 'email',
        'NAME_FIELD': 'name',
        'PROVIDER': 'GitLab',
        'SCOPES': ['read_user'],
    },
    'surfconext-test': {
        'CLIENT_ID': '',
        'CLIENT_SECRET': '',
        'AUTHORIZATION_BASE_URL': 'https://connect.test.surfconext.nl/oidc/authorize',
        'TOKEN_URL': 'https://connect.test.surfconext.nl/oidc/token',
        'USERINFO_URL': 'https://connect.test.surfconext.nl/oidc/userinfo',
        'ID_FIELD': 'email',
        'NAME_FIELD': 'name',
        'PROVIDER': 'Surf Conext',
        'SCOPES': ['openid'],
    },
    'mock': {
        'CLIENT_ID': 'dev',
        'CLIENT_SECRET': 'dev_secret',
        'AUTHORIZATION_BASE_URL': 'http://localhost:8080/authorize',
        'TOKEN_URL': 'http://localhost:8080/token',
        'USERINFO_URL': 'http://localhost:8080/user',
        'ID_FIELD': 'email',
        'NAME_FIELD': 'name',
        'PROVIDER': 'Mock Server',
    },
    'test': {
        'CLIENT_ID': 'test',
        'CLIENT_SECRET': 'test_secret',
        'AUTHORIZATION_BASE_URL': 'https://test.com/oauth/start',
        'TOKEN_URL': 'https://test.com/oauth/token',
        'USERINFO_URL': 'https://test.com/oauth/userinfo',
        'ID_FIELD': 'email',
        'NAME_FIELD': 'name',
        'PROVIDER': 'Mock Server',
        'SCOPES': [],
    }
}
