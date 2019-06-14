import numpy as np
import os

from .image_extraction import extract_images
from PIL import Image
from flask import current_app


def set_blank(copy_number, exam_id, dpi):
    app_config = current_app.config
    data_directory = app_config.get('DATA_DIRECTORY', 'data')
    output_directory = os.path.join(data_directory, f'{exam_id}_data')

    pdf_path = os.path.join(output_directory, 'generated_pdfs', f'{copy_number:05d}.pdf')
    pages = extract_images(pdf_path, dpi)

    for image, page in pages:
        save_image(np.array(image), page, dpi, exam_id, output_directory)


def save_image(image, page, dpi, exam_id, output_directory):
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
