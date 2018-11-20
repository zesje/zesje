import os

import pytest
import numpy as np
import PIL.Image
from tempfile import NamedTemporaryFile
from pony.orm import db_session
from io import BytesIO
import wand.image

from zesje.scans import decode_barcode, ExamMetadata, ExtractedBarcode
from zesje.database import db, _generate_exam_token
from zesje.database import Exam, ExamWidget, Submission
from zesje import scans
from zesje import pdf_generation


# Returns the original image instead of retrieving a box from it
@pytest.fixture
def mock_get_box_return_original(monkeypatch, datadir):
    def mock_return(image, widget, padding):
        return image
    monkeypatch.setattr(scans, 'get_box', mock_return)


# Return a mock DB which can be used in the testing enviroment
# Module scope ensures it is ran only once
@pytest.fixture(scope="module")
def db_setup():
    try:
        db.bind('sqlite', ':memory:')
    except TypeError:
        pass
    else:
        db.generate_mapping(check_tables=False)
    db.drop_all_tables(with_all_data=True)
    db.create_tables()


# Fixture which empties the database
@pytest.fixture
def db_empty(db_setup):
    db.drop_all_tables(with_all_data=True)
    db.create_tables()


# Tests whether the output of calc angle is correct
@pytest.mark.parametrize('image_filename, token, expected', [
    ('COOLTOKEN_0005_01.png', 'COOLTOKEN',
        ExtractedBarcode('COOLTOKEN',   5,   1)),
    ('COOLTOKEN_0050_10.png', 'COOLTOKEN',
        ExtractedBarcode('COOLTOKEN',   50, 10)),
    ('TOKENCOOL_9999_99.png', 'TOKENCOOL',
        ExtractedBarcode('TOKENCOOL', 9999, 99))],
    ids=['Simple test 1', 'Simple test 2', 'High numbers'])
def test_decode_barcode(
        datadir, image_filename, token,
        expected, mock_get_box_return_original):

    image_path = os.path.join(datadir, 'datamatrices', image_filename)

    exam_config = ExamMetadata(
        token=token,
        barcode_coords=[0],
    )

    image = np.array(PIL.Image.open(image_path))

    assert decode_barcode(image, exam_config) == (expected, False)


# Page Generation Functions


def generate_page(width=592, height=842):
    """
    Generate blank page
    by default 72 DPI such that pixels match points
    """
    pdf = np.zeros((height, width))
    pdf.fill(255)
    return PIL.Image.fromarray(pdf).convert("RGB")


def generate_multiple_pages(pages=5):
    return [generate_page() for _ in range(pages)]


# Helper functions



def make_db_entry():
    """
    Default code for generating a database entry
    This needs to be ran at the start of every pipeline test
    TODO: rewrite to a fixture
    """
    with db_session:
        token = _generate_exam_token()
        e = Exam(name="testExam", token=token)
        Submission(copy_number=145, exam=e)
        ExamWidget(exam=e, name='student_id_widget', x=0, y=0)
        exam_config = ExamMetadata(
            token=token,
            barcode_coords=[40, 90, 510, 560],  # in points (not pixels!)
        )
    return exam_config


def generate_pdf(exam_config, pages):
    token = exam_config.token
    datamatrix_x = exam_config.barcode_coords[2]
    datamatrix_y = exam_config.barcode_coords[0]
    pdf = generate_multiple_pages(pages)  # Returns PIL white paper
    with NamedTemporaryFile(suffix='.pdf') as blank, \
            NamedTemporaryFile(suffix='.pdf') as generated:
        pdf[0].save(blank.name, save_all=True, append_images=pdf[1:])
        pdf_generation.generate_pdfs(
            blank.name, token, [145], [generated.name],
            200, 200, datamatrix_x, datamatrix_y)
        genPDF = makeflatpdf(generated.name)
        return genPDF


def makeflatpdf(pdf):
    with wand.image.Image(file=open(pdf, 'rb')) as img:
        images = [wand.image.Image(i) for i in img.sequence]
        for image in images:
            image.format = 'jpg'
        output_pdf = wand.image.Image()
        for image in images:
            output_pdf.sequence.append(image)
        return output_pdf


def makeImage(img):
    images = [wand.image.Image(i) for i in img.sequence]
    for image in images:
        img = PIL.Image.open(BytesIO(image.make_blob("png")))
        img = img.convert('RGB')
        yield img


# Noise transformations


def apply_whitenoise(img, threshold=0.02):
    pix = np.array(img)
    print(pix)
    print(pix.shape)
    noise = 1 - threshold * np.random.rand(*pix.shape)
    data = pix * noise
    return PIL.Image.fromarray(np.uint8(data))


def apply_scan(img, rotation=0, scale=1, skew=(0, 0)):
    """
    Function which can apply different scanning artifacts
    These artifacts include rotation, scaling and skewing
    -------
    img: PIL Image, input image
    rotation: int, Degrees (rotates counterclockwise)
    scale: float, scaling factor w.r.t. img
    skew: int tuple (dx, dy), displace img with dx and dy
    """
    width, height = img.size
    dst = PIL.Image.new("RGBA", img.size, "white")
    new_size = (int(scale * width), int(scale * height))
    img = img.convert("RGBA")
    img = img.resize(new_size, resample=1)
    img = img.rotate(rotation)
    dst.paste(img, skew, mask=img)
    return dst.convert("RGB")


# Pipeline tests:
# General strucuture:
#     1. Make/clean Database
#     2. Make database entry
#     3. Generate PDF with DB token
#     4. Yield generated pdf pages
#     5. Apply transormations (optional)
#     6. Verify scans can be read (or not)


def test_pipeline(db_empty, datadir):
    exam_config = make_db_entry()
    genPDF = generate_pdf(exam_config, 5)
    for image in makeImage(genPDF):
        success, reason = scans.process_page(image, exam_config, datadir)
        assert success is True, reason


@pytest.mark.parametrize('threshold, expected', [
    (0.02, True),
    (0.12, True),
    (0.92, False)],
    ids=['Low noise', 'Medium noise', 'High noise'])
def test_noise(db_empty, datadir, threshold, expected):
    exam_config = make_db_entry()
    genPDF = generate_pdf(exam_config, 1)
    for image in makeImage(genPDF):
        image = apply_whitenoise(image, threshold)
        success, reason = scans.process_page(image, exam_config, datadir)
        assert success is expected, reason


@pytest.mark.parametrize('rotation, expected', [
    (-2, True),
    (0.5, True),
    (0.8, True),
    (2, False)],
    ids=['Large rot', 'Small rot', 'Medium rot', 'failing rot'])
def test_rotate(db_empty, datadir, rotation, expected):
    exam_config = make_db_entry()
    genPDF = generate_pdf(exam_config, 1)
    for image in makeImage(genPDF):
        image = apply_scan(img=image, rotation=rotation)
        #  image.show()
        success, reason = scans.process_page(image, exam_config, datadir)
        assert success is expected, reason


@pytest.mark.parametrize('scale, expected', [
    (0.99, True),
    (1.1, False)],
    ids=['smaller scale', 'larger scale'])
def test_scale(db_empty, datadir, scale, expected):
    exam_config = make_db_entry()
    genPDF = generate_pdf(exam_config, 1)
    for image in makeImage(genPDF):
        image = apply_scan(img=image, scale=scale)
        #  image.show()
        success, reason = scans.process_page(image, exam_config, datadir)
        assert success is expected, reason


@pytest.mark.parametrize('skew, expected', [
    ((10, 10), True),
    ((-10, -5), True)],
    ids=['small skew', 'larger skew'])
def test_skew(db_empty, datadir, skew, expected):
    exam_config = make_db_entry()
    genPDF = generate_pdf(exam_config, 1)
    for image in makeImage(genPDF):
        image = apply_scan(img=image, skew=skew)
        #  image.show()
        success, reason = scans.process_page(image, exam_config, datadir)
        assert success is expected, reason


@pytest.mark.parametrize('rotation, scale, skew, expected', [
    (0.5, 0.99, (10, 10), True),
    (0.5, 1.01, (-10, -5), True)],
    ids=['1st full test', 'second full test'])
def test_all_effects(
        db_empty, datadir, rotation,
        scale, skew, expected):
    exam_config = make_db_entry()
    genPDF = generate_pdf(exam_config, 1)
    for image in makeImage(genPDF):
        image = apply_scan(
            img=image, rotation=rotation, scale=scale, skew=skew)
        #  image.show()
        success, reason = scans.process_page(image, exam_config, datadir)
        assert success is expected, reason
