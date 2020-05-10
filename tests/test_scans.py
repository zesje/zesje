import os

import pytest
import numpy as np
import PIL.Image
import cv2
from tempfile import NamedTemporaryFile
from pikepdf import Pdf
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

from zesje.scans import decode_barcode, ExamMetadata, ExtractedBarcode, exam_metadata, guess_dpi
from zesje.image_extraction import extract_image_pikepdf, extract_images
from zesje.database import db
from zesje.api.exams import generate_exam_token, _exam_generate_data
from zesje.pdf_generation import get_exam_dir, write_finalized_exam, generate_single_pdf
from zesje.database import Exam, ExamWidget
from zesje import scans
from zesje.constants import PAGE_FORMATS


# Returns the original image instead of retrieving a box from it
@pytest.fixture
def mock_get_box_return_original(monkeypatch):
    def mock_return(image, widget, padding):
        return image
    monkeypatch.setattr(scans, 'get_box', mock_return)


@pytest.fixture(scope='module')
def full_app(module_app):
    """
    Default code for generating a database entry and writing
    a finalized exam pdf.
    This needs to be ran at the start of every pipeline test
    """
    exam = Exam(name='Exam')
    db.session.add(exam)
    db.session.commit()

    exam.token = generate_exam_token(exam.id, exam.name, b'EXAM PDF DATA')
    ExamWidget(exam=exam, name='student_id_widget', x=50, y=50)
    ExamWidget(exam=exam, name='barcode_widget', x=40, y=510)

    db.session.commit()

    exam_dir = get_exam_dir(exam.id)
    os.makedirs(exam_dir, exist_ok=True)

    exam_path = os.path.join(exam_dir, 'exam.pdf')
    pdf = canvas.Canvas(exam_path, pagesize=A4)
    for _ in range(2):
        pdf.showPage()
    pdf.save()

    write_finalized_exam(exam)

    yield module_app


def generate_flat_scan_data(copy_number=145):
    """Generates a submission PDF and flattens it"""
    exam = Exam.query.first()
    exam_dir, _, barcode_widget, exam_path, _ = _exam_generate_data(exam)

    exam_config = exam_metadata(exam.id)

    with NamedTemporaryFile() as scan_pdf:
        generate_single_pdf(exam, copy_number, copy_number, scan_pdf)
        scan_pdf.seek(0)

        for image, _ in extract_images(scan_pdf.name, dpi=150):
            yield image, exam_config, exam_dir


def original_page_size(format, dpi):
    h = (PAGE_FORMATS[format][1])/72 * dpi
    w = (PAGE_FORMATS[format][0])/72 * dpi

    return np.rint([h, w]).astype(int)


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


# Noise transformations


def apply_whitenoise(img, threshold=0.02):
    pix = np.array(img)
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
    img = img.resize(new_size, resample=PIL.Image.LANCZOS)
    img = img.rotate(rotation)
    dst.paste(img, skew, mask=img)
    return dst.convert("RGB")


# Pipeline tests:
# General strucuture:
#     1. Make/clean Database
#     2. Make database entry
#     3. Generate PDF with DB token
#     4. Yield generated pdf pages
#     5. Apply transformations (optional)
#     6. Verify scans can be read (or not)


def test_pipeline(full_app):
    for image, exam_config, exam_dir in generate_flat_scan_data():
        success, reason = scans.process_page(image, exam_config, exam_dir)
        assert success is True, reason


@pytest.mark.parametrize('threshold, expected', [
    (0.02, True),
    (0.12, True),
    (0.28, True)],
    ids=['Low noise', 'Medium noise', 'High noise'])
def test_noise(full_app, threshold, expected):
    for image, exam_config, _ in generate_flat_scan_data():
        image = apply_whitenoise(image, threshold)
        success, reason = scans.process_page(image, exam_config)
        assert success is expected, reason


@pytest.mark.parametrize('rotation, expected', [
    (-2, True),
    (0.5, True),
    (0.8, True),
    (2, True)],
    ids=['Large rot', 'Small rot', 'Medium rot', 'Large counterclockwise rot'])
def test_rotate(full_app, rotation, expected):
    for image, exam_config, _ in generate_flat_scan_data():
        image = apply_scan(img=image, rotation=rotation)
        success, reason = scans.process_page(image, exam_config)
        assert success is expected, reason


@pytest.mark.parametrize('scale, expected', [
    (0.99, True),
    (1.1, True)],
    ids=['smaller scale', 'larger scale'])
def test_scale(full_app, scale, expected):
    for image, exam_config, _ in generate_flat_scan_data():
        image = apply_scan(img=image, scale=scale)
        success, reason = scans.process_page(image, exam_config)
        assert success is expected, reason


@pytest.mark.parametrize('skew, expected', [
    ((10, 10), True),
    ((-10, -5), True)],
    ids=['small skew', 'larger skew'])
def test_skew(full_app, skew, expected):
    for image, exam_config, _ in generate_flat_scan_data():
        image = apply_scan(img=image, skew=skew)
        success, reason = scans.process_page(image, exam_config)
        assert success is expected, reason


@pytest.mark.parametrize('rotation, scale, skew, expected', [
    (0.5, 0.99, (10, 10), True),
    (0.5, 1.01, (-10, -5), True)],
    ids=['1st full test', 'second full test'])
def test_all_effects(full_app, rotation, scale, skew, expected):
    for image, exam_config, _ in generate_flat_scan_data():
        image = apply_scan(
            img=image, rotation=rotation, scale=scale, skew=skew)
        success, reason = scans.process_page(image, exam_config)
        assert success is expected, reason


@pytest.mark.parametrize('filename,expected', [
    ['blank-a4-2pages.pdf', ValueError],
    ['single-image-a4.pdf', ValueError],
    ['two-images-a4.pdf', ValueError],
    ['flattened-a4-2pages.pdf', None]],
    ids=['blank pdf', 'single image', 'two images', 'flattened pdf'])
def test_image_extraction_pike(datadir, filename, expected):
    file = os.path.join(datadir, filename)
    with Pdf.open(file) as pdf_reader:
        for page in pdf_reader.pages:
            if expected is not None:
                with pytest.raises(expected):
                    extract_image_pikepdf(page)
            else:
                img = extract_image_pikepdf(page)
                assert img is not None


@pytest.mark.parametrize('filename', [
    'blank-a4-2pages.pdf',
    'flattened-a4-2pages.pdf'],
    ids=['blank pdf', 'flattened pdf'])
def test_image_extraction(datadir, filename):
    file = os.path.join(datadir, filename)
    page = 0
    for img, pagenr in scans.extract_images(file):
        page += 1
        assert pagenr == page
        assert img is not None
        assert np.average(np.array(img)) == 255
    assert page == 2


@pytest.mark.parametrize('file_name, markers', [("a4-rotated.png", [(59, 59), (1181, 59), (59, 1695), (1181, 1695)]),
                                                ("a4-3-markers.png", [(1181, 59), (59, 1695), (1181, 1695)]),
                                                ("a4-rotated-3-markers.png", [(1181, 59), (59, 1695), (1181, 1695)]),
                                                ("a4-rotated-2-markers.png", [(1181, 59), (59, 1695)]),
                                                ("a4-rotated-2-bottom-markers.png", [(59, 1695), (1181, 1695)]),
                                                ("a4-shifted-1-marker.png", [(59, 1695)])
                                                ])
def test_realign_image(config_app, datadir, file_name, markers):
    dir_name = "cornermarkers"
    epsilon = 1

    test_file = os.path.join(datadir, dir_name, file_name)
    test_image = np.array(PIL.Image.open(test_file))

    dpi = guess_dpi(test_image)
    page_shape = np.array(original_page_size('A4', dpi))

    result_image = scans.realign_image(test_image, page_shape)

    result_corner_markers = scans.find_corner_marker_keypoints(result_image)
    assert result_corner_markers is not None
    assert len(result_corner_markers) == len(markers)
    for i in range(len(markers)):
        diff = np.absolute(np.subtract(markers[i], result_corner_markers[i]))
        assert diff[0] <= epsilon
        assert diff[1] <= epsilon


def test_incomplete_reference_realign_image(config_app, datadir):
    dir_name = "cornermarkers"
    epsilon = 1
    test_file = os.path.join(datadir, dir_name, "a4-rotated.png")
    test_image = cv2.imread(test_file)

    correct_corner_markers = [(59, 59), (1181, 59), (59, 1695), (1181, 1695)]

    dpi = guess_dpi(test_image)
    page_shape = np.array(original_page_size('A4', dpi))

    result_image = scans.realign_image(test_image, page_shape)
    result_corner_markers = scans.find_corner_marker_keypoints(result_image)

    assert result_corner_markers is not None
    assert len(result_corner_markers) == len(correct_corner_markers)

    for i in range(4):
        diff = np.absolute(np.subtract(correct_corner_markers[i], result_corner_markers[i]))
        assert diff[0] <= epsilon
        assert diff[1] <= epsilon
