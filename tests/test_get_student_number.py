import os
import cv2

from zesje import scans


# Tests the accuracy and precision of the system for a number of test data.
# More test data should be added. If done, maybe also consider increasing
# the threshold in the assert.
def test_get_studentnumber_precision(config_app, datadir):
    im_names = os.listdir(os.path.join(datadir, 'studentnumbers'))
    for filename_full in im_names:
        im_path = os.path.join(datadir, 'studentnumbers', f'{filename_full}')
        image = cv2.imread(im_path)
        filename_short, _ = os.path.splitext(filename_full)
        expected_number = int(filename_short)
        detected_number = scans.get_student_number(image, [50, 231, 50, 363])
        assert(expected_number == detected_number)
