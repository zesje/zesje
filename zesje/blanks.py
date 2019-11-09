import numpy as np
import os

from .image_extraction import extract_images
from .images import get_box
from PIL import Image
from flask import current_app


def reference_image(problem, dpi, widget_area_in):
    """Returns a reference image for a problem

    The reference image is a flattened image of the
    problem on the original PDF

    Parameters
    ----------
    problem : Problem
        The problem to get the reference image for
    dpi : int
        The desired DPI of the image
    base_path : string
        The folder corresponding to a correct exam.

    Returns
    -------
    image_path : string
        Location of the image.
    """
    page = problem.widget.page

    app_config = current_app.config
    data_directory = app_config.get('DATA_DIRECTORY', 'data')
    generated_path = os.path.join(data_directory, f'{problem.exam_id}_data', 'blanks', f'{dpi}')

    if not os.path.exists(generated_path):
        _extract_reference_images(dpi, problem.exam_id)

    image_path = os.path.join(generated_path, f'page{page:02d}.jpg')
    blank_page = Image.open(image_path)
    return get_box(np.array(blank_page), widget_area_in, padding=0)


def _extract_reference_images(dpi, exam_id):
    """Extract and save reference images for the specified exam

    Saves the images at:
        {data_directory}/{exam_id}_data/blanks/{dpi}/page{page}.jpg

    Parameters
    ----------
    dpi : int
        The desired DPI for the extracted images
    exam_id : int
        The id of the desired exam
    """
    app_config = current_app.config
    data_directory = app_config.get('DATA_DIRECTORY', 'data')
    output_directory = os.path.join(data_directory, f'{exam_id}_data')
    pdf_path = os.path.join(output_directory, 'exam.pdf')

    pages = extract_images(pdf_path, dpi)

    for image, page in pages:
        _save_image(np.array(image), page, dpi, output_directory)


def _save_image(image, page, dpi, output_directory):
    """Save an image at an appropriate location.

    Saves the images at:
        {output_directory}/blanks/{dpi}/page{page}.jpg

    Parameters
    ----------
    image : numpy array
        Image data.
    page : int
        The corresponding page number, starting at 1.
    dpi : int
        The DPI of the image to save.
    output_directory : path
        The output directory of the exam the page is from.

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