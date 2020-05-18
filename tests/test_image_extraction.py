import pytest

from PIL import Image

from zesje.image_extraction import convert_to_rgb

image_modes = ['RGB', 'RGBA', 'L', 'P', 'CMYK', 'HSV']


@pytest.mark.parametrize('image_mode', image_modes, ids=image_modes)
def test_convert_to_rgb(image_mode):
    image = Image.new(image_mode, (10, 10))

    converted = convert_to_rgb(image)

    assert converted.mode == 'RGB'
    assert converted.size == image.size
