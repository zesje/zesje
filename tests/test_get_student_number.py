import os

import pytest

from zesje import scans

# Mocks


# Returns the original image instead of retrieving a box from it
@pytest.fixture
def mock_get_box_return_original(monkeypatch, datadir):
    def mock_return(image, widget, padding):
        return image
    monkeypatch.setattr(scans, 'get_box', mock_return)


# Tests


# Tests the accuracy and precision of the system for a number of test data.
# More test data should be added. If done, maybe also consider increasing
# the threshold in the assert.
def test_get_studentnumber_precision(datadir, mock_get_box_return_original):
    class MockExamConfig:
        student_id_widget_area = [
            0,
            0,
            0,
            0,
        ]

    im_names = os.listdir(os.path.join(datadir, 'studentnumbers'))
    for filename_full in im_names:
        im_path = os.path.join(datadir, 'studentnumbers', f'{filename_full}')
        filename_short, _ = os.path.splitext(filename_full)
        expected_number = int(filename_short)
        detected_number = scans.get_student_number(im_path, MockExamConfig)
        assert(expected_number == detected_number)
