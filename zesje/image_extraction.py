from io import BytesIO

import numpy as np
from PIL import Image
from pikepdf import Pdf, PdfImage
from tempfile import SpooledTemporaryFile
from wand.image import Image as WandImage


def extract_images(filename, dpi=300):
    """Yield all images from a PDF file.

    Tries to use PikePDF to extract the images from the given PDF. If PikePDF is not able to extract the image from a
    page, it continues to use Wand to flatten the rest of the pages.
    """
    with Pdf.open(filename) as pdf_reader:
        use_wand = False

        for index, page in enumerate(pdf_reader.pages):
            if not use_wand:
                try:
                    # Try to use PikePDF, but catch any error it raises
                    img = extract_image_pikepdf(page)

                except (ValueError, AttributeError):
                    # Fallback to Wand if extracting with PikePDF failed
                    use_wand = True

            if use_wand:
                img = extract_image_wand(page, dpi)

            if img.mode == 'L':
                img = img.convert('RGB')

            yield img, index + 1


def extract_image_pikepdf(page):
    """Extracts an image as a PIL Image from the designated page.

    This method uses PikePDF to extract the image. It works on the assumption that the scan is included as a single
    embedded image within the page. This means that the PDF should include a single embedded image which has the same
    aspect ratio of the complete page. If there is not a single image embedded on the page, or if this image does not
    share the same aspect ratio to the page, a ValueError is thrown.

    Parameters
    ----------
    page: pikepdf.Page
        Page from which to extract the image

    Returns
    -------
    img_array : PIL Image
        The extracted image data

    Raises
    ------
    ValueError
        if not exactly one image is found on the page or the image does not have the same aspect ratio as the page
    AttributeError
        if the MediaBox of a page is not defined
    """
    images = page.images

    # Check whether only one image is embedded within the page.
    if len(images) != 1:
        raise ValueError('Not exactly 1 image present on the page.')
    else:
        pdf_image = PdfImage(images[list(images.keys())[0]])
        pdf_width = float(page.MediaBox[2] - page.MediaBox[0])
        pdf_height = float(page.MediaBox[3] - page.MediaBox[1])

        pdf_ratio = pdf_width / pdf_height
        image_ratio = pdf_image.width / pdf_image.height

        # Check if the aspect ratio of the image is the same as the aspect ratio of the page up to a 3% relative error.
        if abs(pdf_ratio - image_ratio) > 0.03 * pdf_ratio:
            raise ValueError('Image has incorrect dimensions')

        return pdf_image.as_pil_image()


def extract_image_wand(page, dpi):
    """Flattens a page from a PDF to an image array.

    This method uses Wand to flatten the page and creates an image.

    Parameters
    ----------
    page: pikepdf.Page
        Page to extract into an image
    dpi:  int
        The dots per inch of the provided PDF page

    Returns
    -------
    img_array : PIL Image
        The extracted image data
    """

    page_pdf = Pdf.new()
    page_pdf.pages.append(page)

    with SpooledTemporaryFile() as page_file:

        page_pdf.save(page_file)

        with WandImage(blob=page_file._file.getvalue(), format='pdf', resolution=dpi) as page_image:
            page_image.format = 'jpg'
            img_array = np.asarray(bytearray(page_image.make_blob(format="jpg")), dtype=np.uint8)
            img = Image.open(BytesIO(img_array))
            img.load()  # Load the data into the PIL image from the Wand image

    return img
