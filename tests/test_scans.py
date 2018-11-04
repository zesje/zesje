import os

import pytest
import numpy as np
from PIL import Image

from zesje.scans import decode_barcode, ExamMetadata, ExtractedBarcode
from zesje import scans


# Returns the original image instead of retrieving a box from it
@pytest.fixture
def mock_get_box_return_original(monkeypatch, datadir):
    def mock_return(image, widget, padding):
        return image
    monkeypatch.setattr(scans, 'get_box', mock_return)


# Tests whether the output of calc angle is correct
@pytest.mark.parametrize('image_filename, token, expected', [
    ('COOLTOKEN_0005_01.png', 'COOLTOKEN', ExtractedBarcode('COOLTOKEN',   5,   1)),
    ('COOLTOKEN_0050_10.png', 'COOLTOKEN', ExtractedBarcode('COOLTOKEN',   50, 10)),
    ('TOKENCOOL_9999_99.png', 'TOKENCOOL', ExtractedBarcode('TOKENCOOL', 9999, 99))],
    ids=['Simple test 1', 'Simple test 2', 'High numbers'])
def test_decode_barcode(datadir, image_filename, token, expected, mock_get_box_return_original):

    image_path = os.path.join(datadir, 'datamatrices', image_filename)

    exam_config = ExamMetadata(
        token=token,
        barcode_coords=[0],
    )

    image = np.array(Image.open(image_path))

    assert decode_barcode(image, exam_config) == (expected, False)


# Untested:
# - def process_pdf()
# - def extract_images()
# - def write_pdf_status()
# - def process_page()
# - def guess_dpi()
# - def rotate_image()
# - def shift_image()
# - get_student_number()
#   Not tested in this file. See: test_get_studentnumber_precision.py
