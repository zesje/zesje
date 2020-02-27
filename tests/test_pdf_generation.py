import os
from io import BytesIO

import PIL
from PIL import Image
import pytest
from ssim import compute_ssim
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen.canvas import Canvas as RLCanvas
from wand.color import Color as WandColor
from wand.image import Image as WandImage
from pylibdmtx import pylibdmtx

from zesje import pdf_generation


# Mock fixtures #


@pytest.fixture
def mock_generate_datamatrix(monkeypatch, datadir):
    def mock_return(exam_id, page_num, copy_num):
        return PIL.Image.open(os.path.join(datadir, 'datamatrix.png'))
    monkeypatch.setattr(pdf_generation, 'generate_datamatrix', mock_return)


@pytest.fixture
def mock_generate_id_grid(monkeypatch):
    def mock_return(canv, x, y):
        canv.setFont('Helvetica', 14)
        canv.drawString(x * mm, y * mm, 'Beautiful ID Grid')
    monkeypatch.setattr(pdf_generation, 'generate_id_grid', mock_return)


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
def test_add_corner_markers(datadir, tmpdir, pagesize, name, config_app):
    config_app.app_context().push()
    pdf_filename = os.path.join(tmpdir, 'file.pdf')

    canv = RLCanvas(pdf_filename, pagesize=pagesize)
    pdf_generation._add_corner_markers(canv, pagesize)
    canv.save()

    image_filename = os.path.join(datadir, 'cornermarkers', f'{name}.png')
    assert_pdf_and_images_are_equal(pdf_filename,
                                    [PIL.Image.open(image_filename)])


def test_generate_id_grid(datadir, tmpdir, config_app):
    config_app.app_context().push()
    pdf_filename = os.path.join(tmpdir, 'file.pdf')

    canv = RLCanvas(pdf_filename, pagesize=A4)
    pdf_generation.generate_id_grid(canv, 0, 0)
    canv.save()

    image_filename = os.path.join(datadir, 'idwidgettest-1.png')
    assert_pdf_and_images_are_equal(pdf_filename,
                                    [PIL.Image.open(image_filename)],
                                    ssim_threshold=0.95)


def test_generate_pdfs_num_files(datadir, tmpdir, config_app):
    config_app.app_context().push()
    blank_pdf = os.path.join(datadir, 'blank-a4-2pages.pdf')

    num_copies = 3
    copy_nums = range(num_copies)
    paths = map(lambda copy_num: os.path.join(tmpdir, f'{copy_num}.pdf'), copy_nums)

    pdf_generation.generate_pdfs(blank_pdf, copy_nums, paths, 'ABCDEFGHIJKL', 25, 270, 150, 270)

    assert len(tmpdir.listdir()) == num_copies


@pytest.mark.parametrize('checkboxes', [[(300, 100, 1, 'c'), (500, 50, 0, 'd'), (500, 500, 0, 'a'), (250, 200, 1, 'b')],
                         [], [(250, 100, 0, None)]])
def test_generate_checkboxes(datadir, tmpdir, checkboxes, config_app):
    config_app.app_context().push()
    blank_pdf = os.path.join(datadir, 'blank-a4-2pages.pdf')

    num_copies = 1
    copy_nums = range(num_copies)
    paths = map(lambda copy_num: os.path.join(tmpdir, f'{copy_num}.pdf'), copy_nums)
    pdf_generation.generate_pdfs(blank_pdf, copy_nums, paths, 'ABCDEFGHIJKL', 25, 270, 150, 270, checkboxes)

    assert len(tmpdir.listdir()) == num_copies


@pytest.mark.parametrize('name', ['a4', 'square'], ids=['a4', 'square'])
def test_join_pdfs(mock_generate_datamatrix, mock_generate_id_grid,
                   datadir, tmpdir, name):
    directory = os.path.join(datadir, f'test-join-pdfs-{name}')
    paths = [
        os.path.join(directory, '00000.pdf'),
        os.path.join(directory, '00001.pdf')]
    out = os.path.join(tmpdir, 'out.pdf')

    pdf_generation.join_pdfs(out, paths)

    image_filename = os.path.join(datadir, f'blank-{name}.png')
    images = [PIL.Image.open(image_filename)] * 4
    assert_pdf_and_images_are_equal(out, images)


def test_generate_datamatrix():
    # Checks for input and output formats, as well as string contents.
    datamatrix = pdf_generation.generate_datamatrix('ABCD', 2, 3)
    assert isinstance(datamatrix, Image.Image)
    assert pylibdmtx.decode(datamatrix)[0].data.decode('utf-8') == 'ABCD/0003/02'
