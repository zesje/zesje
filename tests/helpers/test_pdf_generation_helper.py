import os
from io import BytesIO

import PIL
import pytest
from ssim import compute_ssim
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen.canvas import Canvas as RLCanvas
from wand.color import Color as WandColor
from wand.image import Image as WandImage

from zesje.helpers import pdf_generation_helper


# Mock fixtures #


@pytest.fixture
def mock_generate_datamatrix(monkeypatch, datadir):
    def mock_return(exam_id, page_num, copy_num):
        return PIL.Image.open(os.path.join(datadir, 'datamatrix.png'))
    monkeypatch.setattr(pdf_generation_helper, 'generate_datamatrix',
                        mock_return)


@pytest.fixture
def mock_generate_id_grid(monkeypatch):
    def mock_return(canv, x, y):
        canv.setFont('Helvetica', 14)
        canv.drawString(x * mm, y * mm, 'Beautiful ID Grid')
    monkeypatch.setattr(pdf_generation_helper, 'generate_id_grid', mock_return)


# Utility methods #


# Method to check whether the pages in a PDF are equal to a list of images.
def assert_pdf_and_images_are_equal(pdf_filename, images,
                                    ssim_threshold=0.9985):
    images_pdf = []
    with WandImage(filename=pdf_filename, resolution=150) as pdf:
        for i, page in enumerate(pdf.sequence):
            with WandImage(page) as img:
                img.background_color = WandColor('white')
                img.alpha_channel = 'remove'
                blob = img.make_blob(format='bmp')
                pil_image = PIL.Image.open(BytesIO(blob)).convert(mode='RGB')
                images_pdf.append(pil_image)

    images_input = [x.convert(mode='RGB') for x in images]

    assert len(images_pdf) == len(images_input)

    # For some reason, the images never match exactly, there seems to be a
    # subtle (not visible to the human eye) difference. Therefore, we use the
    # similarity metric SSIM to compare images.
    # For some examples of SSIM, see the section 'Demonstration' at
    # http://www.cns.nyu.edu/~lcv/ssim/
    for i in range(len(images_pdf)):
        assert compute_ssim(images_pdf[i], images_input[i]) >= ssim_threshold


# Tests #


@pytest.mark.parametrize('pagesize,name', [
    (A4, 'a4'),
    ((200 * mm, 200 * mm), 'square')
], ids=['a4', 'square'])
def test_add_corner_markers_and_bottom_bar(datadir, tmpdir, pagesize, name):
    pdf_filename = os.path.join(tmpdir, 'file.pdf')

    canv = RLCanvas(pdf_filename, pagesize=pagesize)
    pdf_generation_helper._add_corner_markers_and_bottom_bar(canv, pagesize)
    canv.save()

    image_filename = os.path.join(datadir, 'cornermarkers', f'{name}.png')
    assert_pdf_and_images_are_equal(pdf_filename,
                                    [PIL.Image.open(image_filename)])


def test_generate_id_grid(datadir, tmpdir):
    pdf_filename = os.path.join(tmpdir, 'file.pdf')

    canv = RLCanvas(pdf_filename, pagesize=A4)
    pdf_generation_helper.generate_id_grid(canv, 0, 0)
    canv.save()

    image_filename = os.path.join(datadir, 'idwidgettest-1.png')
    assert_pdf_and_images_are_equal(pdf_filename,
                                    [PIL.Image.open(image_filename)],
                                    ssim_threshold=0.95)


@pytest.mark.parametrize('pagesize,name', [
    (A4, 'a4'),
    ((200 * mm, 200 * mm), 'square')
], ids=['a4', 'square'])
def test_generate_overlay(mock_generate_datamatrix, mock_generate_id_grid,
                          datadir, tmpdir, pagesize, name):
    filename = os.path.join(str(tmpdir), 'file.pdf')

    canv = RLCanvas(filename, pagesize=pagesize)
    pdf_generation_helper._generate_overlay(canv, pagesize, 'ABCDEFGHIJKL', 1,
                                            2, 25, 150, 125, 150)
    canv.save()

    img_filenames = [os.path.join(datadir, 'overlays', f'{name}-{i}.png')
                     for i in [0, 1]]
    images = [PIL.Image.open(x) for x in img_filenames]
    assert_pdf_and_images_are_equal(filename, images)


def test_generate_pdfs_num_files(datadir, tmpdir):
    blank_pdf = os.path.join(datadir, 'blank-a4-2pages.pdf')

    num_copies = 3

    pdf_generation_helper.generate_pdfs(blank_pdf, 'ABCDEFGHIJKL', str(tmpdir),
                                        num_copies, 25, 270, 150, 270)

    assert len(tmpdir.listdir()) == num_copies


@pytest.mark.parametrize('pagesize,name', [
    (A4, 'a4'),
    ((200 * mm, 200 * mm), 'square')
], ids=['a4', 'square'])
def test_generate_pdfs_blank(mock_generate_datamatrix, mock_generate_id_grid,
                             datadir, tmpdir, pagesize, name):
    blank_pdf = os.path.join(datadir, f'blank-{name}-2pages.pdf')

    pdf_generation_helper.generate_pdfs(blank_pdf, 'ABCDEFGHIJKL', str(tmpdir),
                                        2, 25, 150, 125, 150)

    img_filenames = [os.path.join(datadir, 'overlays', f'{name}-{i}.png')
                     for i in [0, 1]]
    images = [PIL.Image.open(x) for x in img_filenames]
    filenames = [os.path.join(tmpdir, x) for x in ['00000.pdf', '00001.pdf']]
    assert_pdf_and_images_are_equal(filenames[0], images)
    assert_pdf_and_images_are_equal(filenames[1], images)


def test_generate_pdfs_nonblank(mock_generate_datamatrix, mock_generate_id_grid,
                                datadir, tmpdir):
    exam_pdf = os.path.join(datadir, 'exam-2pages.pdf')

    pdf_generation_helper.generate_pdfs(exam_pdf, 'ABCDEFGHIJKL', str(tmpdir),
                                        2, 25, 150, 125, 150)

    img_filenames = [os.path.join(datadir, f'generated-{i}.png')
                     for i in [0, 1]]
    images = [PIL.Image.open(x) for x in img_filenames]
    for pdf_name in ['00000.pdf', '00001.pdf']:
        assert_pdf_and_images_are_equal(os.path.join(tmpdir, pdf_name), images)


def test_generate_pdfs_black(mock_generate_datamatrix, mock_generate_id_grid,
                             datadir, tmpdir):
    black_pdf = os.path.join(datadir, 'black-a4-2pages.pdf')

    pdf_generation_helper.generate_pdfs(black_pdf, 'ABCDEFGHIJKL', str(tmpdir),
                                        2, 25, 150, 125, 150)

    images = [PIL.Image.open(os.path.join(datadir, 'generated-black.png'))] * 2
    for pdf_name in ['00000.pdf', '00001.pdf']:
        assert_pdf_and_images_are_equal(os.path.join(tmpdir, pdf_name), images)


def test_generate_pdfs_exam_is_file(mock_generate_datamatrix, mock_generate_id_grid, datadir, tmpdir):
    blank_pdf = open(os.path.join(datadir, f'blank-a4-2pages.pdf'), 'rb')

    pdf_generation_helper.generate_pdfs(blank_pdf, 'ABCDEFGHIJKL', str(tmpdir),
                                        2, 25, 150, 125, 150)

    img_filenames = [os.path.join(datadir, 'overlays', f'a4-{i}.png') for i in [0, 1]]
    images = [PIL.Image.open(x) for x in img_filenames]
    filenames = [os.path.join(tmpdir, x) for x in ['00000.pdf', '00001.pdf']]
    assert_pdf_and_images_are_equal(filenames[0], images)
    assert_pdf_and_images_are_equal(filenames[1], images)


@pytest.mark.parametrize('name', ['a4', 'square'], ids=['a4', 'square'])
def test_join_pdfs(mock_generate_datamatrix, mock_generate_id_grid,
                   datadir, tmpdir, name):
    directory = os.path.join(datadir, f'test-join-pdfs-{name}')
    out = os.path.join(tmpdir, 'out.pdf')
    num_copies = 2

    pdf_generation_helper.join_pdfs(directory, out, num_copies)

    image_filename = os.path.join(datadir, f'blank-{name}.png')
    images = [PIL.Image.open(image_filename)] * 4
    assert_pdf_and_images_are_equal(out, images)


# Untested:
#
# - generate_datamatrix()
#   Given a single data string, there may be many generated DataMatrix codes
#   that correspond to that string. Therefore, a test to check the generated
#   DataMatrix code would break if we ever move to a different encoding library
#   or if the current library ever implements a more efficient encoding
#   algorithm. A test for this function would therefore be brittle.
#   Furthermore, the function is very short, so the need for testing is not
#   very high.
