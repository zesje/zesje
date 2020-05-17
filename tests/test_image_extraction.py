import pytest
import zipfile

from pathlib import Path
from io import BytesIO
from PIL import Image

from zesje.image_extraction import convert_to_rgb, extract_pages_from_file, guess_page_info, guess_missing_page_info
from zesje.database import Student

image_modes = ['RGB', 'RGBA', 'L', 'P', 'CMYK', 'HSV']


@pytest.mark.parametrize('image_mode', image_modes, ids=image_modes)
def test_convert_to_rgb(image_mode):
    image = Image.new(image_mode, (10, 10))

    converted = convert_to_rgb(image)

    assert converted.mode == 'RGB'
    assert converted.size == image.size


@pytest.mark.parametrize('file_info, info', [
    (['1234567-02.png'], (1234567, 1, None)),
    (['1234567-1-4.jpeg'], (1234567, 0, 4)),
    (['1234567.png'], (1234567, None, None)),
    (['ABCDEFG.jpeg'], (None, None, None)),
    (['1234567.zip', '1.png'], (1234567, 0, None)),
    (['1234567.zip', '1-2.jpg'], (1234567, 0, 2)),
    (['1234567.pdf', 1], (1234567, 0, None)),
    (['some.zip', '1234567.pdf', 2], (1234567, 1, None)),
    (['some.zip', '1234567/2.pdf', 2], (1234567, 1, 2)),
    (['some.zip', '1234567-1.jpg'], (1234567, 0, None)),
    (['some.zip', '1234567/1.png'], (1234567, 0, None)),
    (['some.zip', 'Random First Last 99 Januari 99/submission.pdf', 3], (1000001, 2, None))
    ],
    ids=[
    'Valid name (no copy)',
    'Valid name (with copy)',
    'Valid name (no page)',
    'Invalid name (no student)',
    'Valid name (no copy, img in zip)',
    'Valid name (with copy, img in zip)',
    'Valid name (pdf)',
    'Valid name (pdf in zip)',
    'Valid name (copy in pdf in zip)',
    'Valid name (img page in zip)',
    'Valid name (img in folder in zip',
    'Valid name (pdf in folder (student name) in zip'])
def test_guess_image_info(file_info, info):
    students = [
        Student(id=1000001, first_name='First', last_name='Last')
    ]
    try:
        ext_info = guess_page_info(file_info, students)
    except Exception:
        ext_info = None

    assert ext_info == info


def test_guess_missing_page_info():
    page_infos = [
        (None, None, None),
        (1000000, 0, None), (1000000, 1, None),
        (1000001, 0, None), (1000001, 1, 1),
        (1000002, None, None), (1000002, 1, 1),
        (1000003, 1, None), (1000003, 1, None),
        (1000004, 1, 1), (1000004, 1, 2),
        (1000005, None, None),
        (1000006, None, None), (1000006, None, None),
        (1000007, 0, None), (1000007, 0, 2),
        (1000008, 0, None), (1000008, 0, 1)
    ]
    fixed_page_infos = guess_missing_page_info(page_infos)
    assert fixed_page_infos == [
        (None, None, None),
        (1000000, 0, 1), (1000000, 1, 1),
        (1000001, 0, 1), (1000001, 1, 1),
        (1000002, 0, 1), (1000002, 1, 1),
        (1000003, None, None), (1000003, None, None),
        (1000004, 1, 1), (1000004, 1, 2),
        (1000005, 0, 1),
        (1000006, None, None), (1000006, None, None),
        (1000007, 0, 1), (1000007, 0, 2),
        (1000008, None, None), (1000008, None, None)
    ]


def test_extract_pages_no_image(app):
    file_content = b'1701'
    result = [result for result in extract_pages_from_file(file_content, 'notanimage.nopng')]
    assert len(result) == 1

    image, page_info, file_info, number, total = result[0]
    assert not isinstance(image, Image.Image)
    assert image == file_content
    assert number == 1
    assert total == 1


def test_extract_pages_from_zip(app):
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
        pages = [0, 1]
        for expected_number, (image, page_info, file_info, number, total) in enumerate(
            extract_pages_from_file(zip_bytes, 'scan.zip'), start=1
        ):
            assert isinstance(image, Image.Image)
            assert image.size == (10, 10)
            assert number == expected_number
            assert number <= total
            assert total >= last_total
            last_total = total

            student, page, copy = page_info
            assert student == 1000000
            assert page in pages
            pages.pop(pages.index(page))
            assert copy == 1

        assert last_total == 2


def test_extract_images_from_pdf(app, datadir):
    flat_pdf = Path(datadir) / 'flattened-a4-2pages.pdf'
    last_total = 0
    for expected_number, (image, page_info, file_info, number, total) in enumerate(
        extract_pages_from_file(flat_pdf, flat_pdf, dpi=72), start=1
    ):
        assert isinstance(image, Image.Image)
        assert image.size == (827, 1169)
        assert number == expected_number
        assert number <= total
        assert total >= last_total
        last_total = total

        assert page_info == (None, None, None)

    assert last_total == 2


def test_extract_images_from_mixed_zip(app, datadir):
    flat_pdf = Path(datadir) / 'flattened-a4-2pages.pdf'
    with BytesIO() as zip_bytes:
        with zipfile.ZipFile(zip_bytes, 'w') as z, \
            BytesIO() as image_bytes, \
                Image.new('RGB', (10, 10)) as image:

            image.save(image_bytes, format='png')
            image_bytes.seek(0)
            z.writestr('1000000-4.png', image_bytes.read())
            image_bytes.seek(0)
            z.writestr('1000000/3.png', image_bytes.read())
            z.writestr('1000000.pdf', flat_pdf.read_bytes())
            z.writestr('1000000/4.txt', b'1701')

        zip_bytes.seek(0)

        last_total = 0
        pages = [0, 1, 2, 3]
        for expected_number, (image, page_info, file_info, number, total) in enumerate(
            extract_pages_from_file(zip_bytes, 'scan.zip'), start=1
        ):
            if isinstance(image, Image.Image):
                assert image.size in [(10, 10), (827, 1169)]
            else:
                assert image.read() == b'1701'
            assert number == expected_number
            assert number <= total
            assert total >= last_total
            last_total = total

            student, page, copy = page_info
            if page is None:
                assert page_info == (None, None, None)
            else:
                assert student == 1000000
                if page is None:
                    assert page_info == (1000000, None, None)
                else:
                    assert page in pages
                    pages.pop(pages.index(page))
                    assert copy == 1

    assert pages == []
    assert last_total == 5
