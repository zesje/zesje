from reportlab.lib.units import mm

# student id widget
ID_GRID_FONT_SIZE = 11  # Size of font
ID_GRID_FONT = 'Helvetica'
ID_GRID_MARGIN = 5  # Margin between elements and sides
ID_GRID_DIGITS = 7  # Max amount of digits you want for student numbers

# copy number widget
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

SQLALCHEMY_TRACK_MODIFICATIONS = False  # Suppress future deprecation warning