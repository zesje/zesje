import pytest
import zipfile

from pathlib import Path
from io import BytesIO
from PIL import Image

from zesje.image_extraction import convert_to_rgb, extract_images_from_file

image_modes = ['RGB', 'RGBA', 'L', 'P', 'CMYK', 'HSV']


@pytest.mark.parametrize('image_mode', image_modes, ids=image_modes)
def test_convert_to_rgb(image_mode):
    image = Image.new(image_mode, (10, 10))

    converted = convert_to_rgb(image)

    assert converted.mode == 'RGB'
    assert converted.size == image.size


def test_extract_images_no_image(config_app):
    file_content = b'1701'
    result = [result for result in extract_images_from_file(file_content, 'notanimage.nopng')]
    assert len(result) == 1

    image, file_info, number, total = result[0]
    assert not isinstance(image, Image.Image)
    assert image == file_content
    assert number == 1
    assert total == 1


def test_extract_images_from_zip(config_app):
    with BytesIO() as zip_bytes:
        with zipfile.ZipFile(zip_bytes, 'w') as z, \
            BytesIO() as image_bytes, \
                Image.new('RGB', (10, 10)) as image:

            image.save(image_bytes, format='png')
            image_bytes.seek(0)
            z.writestr('1000000-1.png', image_bytes.read())
            image_bytes.seek(0)
            z.writestr('1000000/2.png', image_bytes.read())

        zip_bytes.seek(0)

        last_total = 0
        for expected_number, (image, file_info, number, total) in enumerate(
            extract_images_from_file(zip_bytes, 'scan.zip'), start=1
        ):
            assert isinstance(image, Image.Image)
            assert image.size == (10, 10)
            assert number == expected_number
            assert number <= total
            assert total >= last_total
            last_total = total

        assert last_total == 2


def test_extract_images_from_pdf(config_app, datadir):
    flat_pdf = Path(datadir) / 'flattened-a4-2pages.pdf'
    last_total = 0
    for expected_number, (image, file_info, number, total) in enumerate(
        extract_images_from_file(flat_pdf, flat_pdf, dpi=72), start=1
    ):
        assert isinstance(image, Image.Image)
        assert image.size == (827, 1169)
        assert number == expected_number
        assert number <= total
        assert total >= last_total
        last_total = total

    assert last_total == 2


def test_extract_images_from_mixed_zip(config_app, datadir):
    flat_pdf = Path(datadir) / 'flattened-a4-2pages.pdf'
    with BytesIO() as zip_bytes:
        with zipfile.ZipFile(zip_bytes, 'w') as z, \
            BytesIO() as image_bytes, \
                Image.new('RGB', (10, 10)) as image:

            image.save(image_bytes, format='png')
            image_bytes.seek(0)
            z.writestr('1000000-1.png', image_bytes.read())
            image_bytes.seek(0)
            z.writestr('1000000/2.png', image_bytes.read())
            z.writestr('10000001.pdf', flat_pdf.read_bytes())
            z.writestr('10000002.txt', b'1701')

        zip_bytes.seek(0)

        last_total = 0
        for expected_number, (image, file_info, number, total) in enumerate(
            extract_images_from_file(zip_bytes, 'scan.zip'), start=1
        ):
            if isinstance(image, Image.Image):
                assert image.size in [(10, 10), (827, 1169)]
            else:
                assert image == b'1701'
            assert number == expected_number
            assert number <= total
            assert total >= last_total
            last_total = total

    assert last_total == 5
