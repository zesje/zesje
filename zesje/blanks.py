import numpy as np
import os

from .image_extraction import extract_images
from .images import get_box
from PIL import Image
from flask import current_app


def get_blank(problem, dpi, widget_area_in):
    page = problem.widget.page

    app_config = current_app.config
    data_directory = app_config.get('DATA_DIRECTORY', 'data')
    output_directory = os.path.join(data_directory, f'{problem.exam_id}_data')

    generated_path = os.path.join(output_directory, 'blanks', f'{dpi}')

    if not os.path.exists(generated_path):
        set_blank(dpi, output_directory)

    image_path = os.path.join(generated_path, f'page{page:02d}.jpg')
    blank_page = Image.open(image_path)
    return get_box(np.array(blank_page), widget_area_in, padding=0)


def set_blank(dpi, output_directory):
    pdf_path = os.path.join(output_directory, 'exam.pdf')
    pages = extract_images(pdf_path, dpi)

    for image, page in pages:
        save_image(np.array(image), page, dpi, output_directory)


def save_image(image, page, dpi, output_directory):
    """Save an image at an appropriate location.

    Parameters
    ----------
    image : numpy array
        Image data.
    barcode : ExtractedBarcode
        The barcode identifying the page.
    base_path : string
        The folder corresponding to a correct exam.

    Returns
    -------
    image_path : string
        Location of the image.
    """

    submission_path = os.path.join(output_directory, 'blanks', f'{dpi}')
    os.makedirs(submission_path, exist_ok=True)
    image_path = os.path.join(submission_path, f'page{page-1:02d}.jpg')
    Image.fromarray(image).save(image_path)
    return image_path
