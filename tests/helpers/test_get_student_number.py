import pytest
import os
from zesje.helpers import scan_helper

# Mocks


# Returns the original image instead of retrieving a box from it
@pytest.fixture
def mock_get_box_return_original(monkeypatch, datadir):
    def mock_return(image, widget, padding):
        return image
    monkeypatch.setattr(scan_helper, 'get_box',
                        mock_return)


# Tests


# Tests the accuracy and precision of the system for a number of test data.
# More test data should be added. If done, maybe also consider increasing
# the threshold in the assert.
def test_get_studentnumber_precision(datadir, mock_get_box_return_original):
    class MockWidget:
        top = 0
        bottom = 0
        left = 0
        right = 0

    im_names = os.listdir(os.path.join(datadir, 'studentnumbers'))
    count = 0
    for filename_full in im_names:
        im_path = os.path.join(datadir, 'studentnumbers', f'{filename_full}')
        filename_short, _ = os.path.splitext(filename_full)
        expected_number = int(filename_short)
        detected_number = scan_helper.get_student_number(im_path, MockWidget)
        if(expected_number == detected_number):
            count = count + 1

    assert((count / len(im_names)) > 0.8)
