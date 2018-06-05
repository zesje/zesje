import pytest
import numpy as np
from zesje.helpers import image_helper

# Tests


# Tests whether RuntimeError are raised correctly


@pytest.mark.parametrize('keypoints_input, expected_error', [
    ([(0, 0), (750, 750)], True)],
    ids=['Not enough corner markers'])
def test_runtime_error_check_corner_marker(keypoints_input, expected_error):

    image_data = np.zeros((1000, 1000))
    if expected_error:
        with pytest.raises(RuntimeError):
            image_helper.check_corner_keypoints(image_data, keypoints_input)
    else:
        image_helper.check_corner_keypoints(image_data, keypoints_input)
        assert True
