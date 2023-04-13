import pytest
import zipfile

from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from pikepdf import Pdf
from pathlib import Path
from io import BytesIO
from PIL import Image

from zesje.image_extraction import convert_to_rgb, extract_pages_from_file, guess_page_info, guess_missing_page_info
from zesje.image_extraction import extract_image_wand
from zesje.database import Student

image_modes = ["RGB", "RGBA", "L", "P", "CMYK", "HSV"]


@pytest.mark.parametrize("image_mode", image_modes, ids=image_modes)
def test_convert_to_rgb(image_mode):
    image = Image.new(image_mode, (10, 10))

    converted = convert_to_rgb(image)

    assert converted.mode == "RGB"
    assert converted.size == image.size


def test_large_mediabox_limit(app):
    pdf_path = Path(app.config["DATA_DIRECTORY"]) / "large.pdf"
    page_size = (10000, 15000)
    dpi = 300

    pdf = canvas.Canvas(str(pdf_path), pagesize=page_size)
    pdf.showPage()
    pdf.save()

    with Pdf.open(str(pdf_path)) as pdf:
        for page in pdf.pages:
            with pytest.warns(None) as warnings:
                image = extract_image_wand(page, dpi)
            assert not warnings
            assert isinstance(image, Image.Image)
            h, w = image.size
            assert h * w < page_size[0] * page_size[1] * inch**2 * dpi**2


guess_image_info_arguments = [
    (["1234567-02.png"], (1234567, 1, None), "Valid student page"),
    (["1234567-1-4.jpeg"], (1234567, 0, 4), "Valid student page copy"),
    (["1234567.png"], (1234567, None, None), "Valid student"),
    (["ABCDEFG.jpeg"], (None, None, None), "Invalid letter"),
    (["1234567.zip", "1.png"], (1234567, 0, None), "Vallid zip student page"),
    (["1234567.zip", "1-2.jpg"], (1234567, 0, 2), "Valid zip student page copy"),
    (["1234567.pdf", 1], (1234567, 0, None), "Valid pdf student page"),
    (["some.zip", "1234567.pdf", 2], (1234567, 1, None), "Valid scan zip student page"),
    (["some.zip", "1234567/2.pdf", 2], (1234567, 1, 2), "Valid scan zip student page copy"),
    (["some.zip", "1234567-1.jpg"], (1234567, 0, None), "Valid scan zip student page"),
    (["some.zip", "1234567/1.png"], (1234567, 0, None), "Valid scan zip folder student page"),
    (
        ["some.zip", "Random First Last 99 Januari 99/submission.pdf", 3],
        (1000001, 2, None),
        "Valid folder name student page",
    ),
    (
        ["some.zip", "Random First Last 99 Januari 99/1000001.pdf", 3],
        (1000001, 2, None),
        "Valid folder name id student page",
    ),
    (["tn1234.zip", "1234567/final tn1234.pdf", 5], (1234567, 4, None), "Valid scan zip pdf number student page"),
    (["tn1234.zip", "1234567/tn1234 page 1.pdf", 4], (1234567, 0, 4), "Valid scan zip pdf number student page copy"),
    (["tn1234.zip", "1234567/tn1234 page 1 copy 2.png"], (1234567, 0, 2), "Valid scan zip img number student page"),
]


@pytest.mark.parametrize(
    "file_info, info",
    [(file_info, info) for file_info, info, _ in guess_image_info_arguments],
    ids=[id for *_, id in guess_image_info_arguments],
)
def test_guess_image_info(file_info, info):
    students = [Student(id=1000001, first_name="First", last_name="Last")]
    try:
        ext_info = guess_page_info(file_info, students)
    except Exception:
        ext_info = None

    assert ext_info == info


def test_guess_missing_page_info():
    page_infos = [
        (None, None, None),
        (1000000, 0, None),
        (1000000, 1, None),
        (1000001, 0, None),
        (1000001, 1, 1),
        (1000002, None, None),
        (1000002, 1, 1),
        (1000003, 1, None),
        (1000003, 1, None),
        (1000004, 1, 1),
        (1000004, 1, 2),
        (1000005, None, None),
        (1000006, None, None),
        (1000006, None, None),
        (1000007, 0, None),
        (1000007, 0, 2),
        (1000008, 0, None),
        (1000008, 0, 1),
    ]
    fixed_page_infos = guess_missing_page_info(page_infos)
    assert fixed_page_infos == [
        (None, None, None),
        (1000000, 0, 1),
        (1000000, 1, 1),
        (1000001, 0, 1),
        (1000001, 1, 1),
        (1000002, 0, 1),
        (1000002, 1, 1),
        (1000003, None, None),
        (1000003, None, None),
        (1000004, 1, 1),
        (1000004, 1, 2),
        (1000005, 0, 1),
        (1000006, None, None),
        (1000006, None, None),
        (1000007, 0, 1),
        (1000007, 0, 2),
        (1000008, None, None),
        (1000008, None, None),
    ]


def test_extract_pages_no_image(app):
    file_content = b"1701"
    result = list(extract_pages_from_file(file_content, "notanimage.nopng"))
    assert len(result) == 1

    image, page_info, file_info, number, total = result[0]
    assert not isinstance(image, Image.Image)
    assert image == file_content
    assert number == 1
    assert total == 1


def test_extract_pages_corrupted_image(app):
    file_content = b"1701"
    result = list(extract_pages_from_file(file_content, "corrupted_image.png"))
    assert len(result) == 1

    image, page_info, file_info, number, total = result[0]
    assert isinstance(image, Exception)
    assert number == 1
    assert total == 1


def test_extract_pages_corrupted_pdf(app):
    file_content = b"1701"
    result = list(extract_pages_from_file(file_content, "corrupted_pdf.pdf"))
    assert len(result) == 1

    image, page_info, file_info, number, total = result[0]
    assert isinstance(image, Exception)
    assert number == 1
    assert total == 1


def test_extract_pages_from_zip(app):
    with BytesIO() as zip_bytes:
        with zipfile.ZipFile(zip_bytes, "w") as z, BytesIO() as image_bytes, Image.new("RGB", (10, 10)) as image:
            image.save(image_bytes, format="png")
            image_bytes.seek(0)
            z.writestr("1000000-1.png", image_bytes.read())
            image_bytes.seek(0)
            z.writestr("1000000/2.png", image_bytes.read())

        zip_bytes.seek(0)

        last_total = 0
        pages = [0, 1]
        for expected_number, (image, page_info, file_info, number, total) in enumerate(
            extract_pages_from_file(zip_bytes, "scan.zip"), start=1
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
    flat_pdf = Path(datadir) / "flattened-a4-2pages.pdf"
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
    flat_pdf = Path(datadir) / "flattened-a4-2pages.pdf"
    with BytesIO() as zip_bytes:
        with zipfile.ZipFile(zip_bytes, "w") as z, BytesIO() as image_bytes, Image.new("RGB", (10, 10)) as image:
            image.save(image_bytes, format="png")
            image_bytes.seek(0)
            z.writestr("1000000-4.png", image_bytes.read())
            image_bytes.seek(0)
            z.writestr("1000000/3.png", image_bytes.read())
            z.writestr("1000000.pdf", flat_pdf.read_bytes())
            z.writestr("1000000/4.txt", b"1701")

        zip_bytes.seek(0)

        last_total = 0
        pages = [0, 1, 2, 3]
        for expected_number, (image, page_info, file_info, number, total) in enumerate(
            extract_pages_from_file(zip_bytes, "scan.zip"), start=1
        ):
            if isinstance(image, Image.Image):
                assert image.size in [(10, 10), (827, 1169)]
            else:
                assert image.read() == b"1701"
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
