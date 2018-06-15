import pytest
import numpy as np
from zesje.helpers import image_helper

# Tests


# Tests whether RuntimeError are raised correctly


@pytest.mark.parametrize('keypoints_input, error_expected', [
    ([(0, 0), (750, 750)], True),
    ([(0, 0), (750, 0), (0, 750), (750, 750), (250, 250)], True),
    ([(0, 0), (750, 0), (250, 250)], True),
    ([(0, 0), (750, 0), (750, 750)], False)],
    ids=['Not enough corner markers', 'Too many corner',
         'Two markers detected in same corner',
         'Enough markers, evenly spread'])
def test_runtime_error_check_corner_marker(keypoints_input, error_expected):

    image_data = np.zeros((1000, 1000))
    if error_expected:
        with pytest.raises(RuntimeError):
            image_helper.check_corner_keypoints(image_data, keypoints_input)
    else:
        image_helper.check_corner_keypoints(image_data, keypoints_input)
        assert True
