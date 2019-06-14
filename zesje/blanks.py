import cv2
import numpy as np
import os

from .database import db, Exam, Problem
from .images import guess_dpi, get_box
from .scans import extract_images
from PIL import Image
from flask import current_app


def set_blank(pdf_path, exam_id):
    pages = extract_images(pdf_path, 144)
    exam = Exam.query.filter(Exam.token == exam_id).first()
    page_num = 0

    for image, page in pages :
        save_image(np.array(image), page, 144, exam.id)
        problems_on_page = [problem for problem in exam.problems if problem.widget.page == page_num]
        page_num = page_num + 1
        for problem in problems_on_page:
            widget_area = np.asarray([
                problem.widget.y,  # top
                problem.widget.y + problem.widget.height,  # bottom
                problem.widget.x,  # left
                problem.widget.x + problem.widget.width,  # right
            ])
            page_img = np.array(image)
            widget_area_in = widget_area / 72

            cut_im = get_box(page_img, widget_area_in, padding=0)
            gray = cv2.cvtColor(cut_im, cv2.COLOR_BGR2GRAY)

    #        ret,thresh = cv2.threshold(gray,180,255,3)
            input_image = np.array(gray)



def save_image(image, page, dpi, exam_id):
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

    app_config = current_app.config
    data_directory = app_config.get('DATA_DIRECTORY', 'data')
    # blank_storage = os.path.join(data_directory, 'scans', f'{scan.id}.pdf')
    output_directory = os.path.join(data_directory, f'{exam_id}_data')

    submission_path = os.path.join(output_directory, 'blanks', f'{dpi}')
    os.makedirs(submission_path, exist_ok=True)
    image_path = os.path.join(submission_path, f'page{page-1:02d}.jpg')
    Image.fromarray(image).save(image_path)
    return image_path
