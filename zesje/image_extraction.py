from io import BytesIO

import numpy as np
from PIL import Image
from pikepdf import Pdf, PdfImage
from tempfile import SpooledTemporaryFile
from wand.image import Image as WandImage


def extract_images(filename):
    """Yield all images from a PDF file.

    Tries to use PikePDF to extract the images from the given PDF.
    If PikePDF is not able to extract the image from a page,
    it continues to use Wand to flatten the rest of the pages.
    """

    with Pdf.open(filename) as pdf_reader:
        use_wand = False

        total = len(pdf_reader.pages)

        for pagenr in range(total):
            if not use_wand:
                try:
                    # Try to use PikePDF, but catch any error it raises
                    img = extract_image_pikepdf(pagenr, pdf_reader)

                except Exception:
                    # Fallback to Wand if extracting with PikePDF failed
                    use_wand = True

            if use_wand:
                img = extract_image_wand(pagenr, pdf_reader)

            if img.mode == 'L':
                img = img.convert('RGB')

            yield img, pagenr+1


def extract_image_pikepdf(pagenr, reader):
    """Extracts an image as an array from the designated page

    This method uses PikePDF to extract the image and only works
    when there is a single image present on the page with the
    same aspect ratio as the page.

    We do not check for the actual size of the image on the page,
    since this size depends on the draw instruction rather than
    the embedded image object available to pikepdf.

    Raises an error if not exactly image is present or the image
    does not have the same aspect ratio as the page.

    Parameters
    ----------
    pagenr : int
        Page number to extract
    reader : pikepdf.Pdf instance
        The pdf reader to read the page from

    Returns
    -------
    img_array : PIL Image
        The extracted image data

    Raises
    ------
    ValueError
        if not exactly one image is found on the page or the image
        does not have the same aspect ratio as the page
    AttributeError
        if no XObject or MediaBox is present on the page
    """

    page = reader.pages[pagenr]

    xObject = page.Resources.XObject

    if sum((xObject[obj].Subtype == '/Image')
            for obj in xObject) != 1:
        raise ValueError('Not exactly 1 image present on the page')

    for obj in xObject:
        if xObject[obj].Subtype == '/Image':
            pdfimage = PdfImage(xObject[obj])

            pdf_width = float(page.MediaBox[2] - page.MediaBox[0])
            pdf_height = float(page.MediaBox[3] - page.MediaBox[1])

            ratio_width = pdfimage.width / pdf_width
            ratio_height = pdfimage.height / pdf_height

            # Check if the aspect ratio of the image is the same as the
            # aspect ratio of the page up to a 3% relative error
            if abs(ratio_width - ratio_height) > 0.03 * ratio_width:
                raise ValueError('Image has incorrect dimensions')

            return pdfimage.as_pil_image()


def extract_image_wand(pagenr, reader):
    """Flattens a page from a PDF to an image array

    This method uses Wand to flatten the page and creates an image.

    Parameters
    ----------
    pagenr : int
        Page number to extract, starting at 0
    reader : pikepdf.Pdf instance
        The pdf reader to read the page from

    Returns
    -------
    img_array : PIL Image
        The extracted image data
    """
    page = reader.pages[pagenr]

    page_pdf = Pdf.new()
    page_pdf.pages.append(page)

    with SpooledTemporaryFile() as page_file:

        page_pdf.save(page_file)

        with WandImage(blob=page_file._file.getvalue(), format='pdf', resolution=300) as page_image:
            page_image.format = 'jpg'
            img_array = np.asarray(bytearray(page_image.make_blob(format="jpg")), dtype=np.uint8)
            img = Image.open(BytesIO(img_array))
            img.load()  # Load the data into the PIL image from the Wand image

    return img

