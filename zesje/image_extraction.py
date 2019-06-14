from io import BytesIO

import numpy as np
import PyPDF2
from PIL import Image
from wand.image import Image as WandImage


def extract_images(filename, dpi=300):
    """Yield all images from a PDF file.

    Tries to use PyPDF2 to extract the images from the given PDF.
    If PyPDF2 fails to open the PDF or PyPDF2 is not able to extract
    a page, it continues to use Wand for the rest of the pages.
    """

    with open(filename, "rb") as file:
        use_wand = False
        pypdf_reader = None
        wand_image = None
        total = 0

        try:
            pypdf_reader = PyPDF2.PdfFileReader(file)
            total = pypdf_reader.getNumPages()
        except Exception:
            # Fallback to Wand if opening the PDF with PyPDF2 failed
            use_wand = True

        if use_wand:
            # If PyPDF2 failed we need Wand to count the number of pages
            wand_image = WandImage(filename=filename, resolution=dpi)
            total = len(wand_image.sequence)

        for pagenr in range(total):
            if not use_wand:
                try:
                    # Try to use PyPDF2, but catch any error it raises
                    img = extract_image_pypdf(pagenr, pypdf_reader)

                except Exception:
                    # Fallback to Wand if extracting with PyPDF2 failed
                    use_wand = True

            if use_wand:
                if wand_image is None:
                    wand_image = WandImage(filename=filename, resolution=dpi)
                img = extract_image_wand(pagenr, wand_image)

            if img.mode == 'L':
                img = img.convert('RGB')

            yield img, pagenr+1

        if wand_image is not None:
            wand_image.close()


def extract_image_pypdf(pagenr, reader):
    """Extracts an image as an array from the designated page

    This method uses PyPDF2 to extract the image and only works
    when there is a single image present on the page.

    Raises an error if not exactly one image is found on the page
    or the image filter is not `FlateDecode`.

    Adapted from https://stackoverflow.com/a/34116472/2217463

    Parameters
    ----------
    pagenr : int
        Page number to extract
    reader : PyPDF2.PdfFileReader instance
        The reader to read the page from

    Returns
    -------
    img_array : PIL Image
        The extracted image data

    Raises
    ------
    ValueError if not exactly one image is found on the page

    NotImplementedError if the image filter is not `FlateDecode`
    """

    page = reader.getPage(pagenr)
    xObject = page['/Resources']['/XObject'].getObject()

    if sum((xObject[obj]['/Subtype'] == '/Image')
            for obj in xObject) != 1:
        raise ValueError

    for obj in xObject:
        if xObject[obj]['/Subtype'] == '/Image':
            data = xObject[obj].getData()
            filter = xObject[obj]['/Filter']

            if filter == '/FlateDecode':
                size = (xObject[obj]['/Width'], xObject[obj]['/Height'])
                if xObject[obj]['/ColorSpace'] == '/DeviceRGB':
                    mode = "RGB"
                else:
                    mode = "P"
                img = Image.frombytes(mode, size, data)
            else:
                raise NotImplementedError

            return img


def extract_image_wand(pagenr, wand_image):
    """Flattens a page from a PDF to an image array

    This method uses Wand to flatten the page and extract the image.

    Parameters
    ----------
    pagenr : int
        Page number to extract, starting at 0
    wand_image : Wand Image instance
        The Wand Image to read from

    Returns
    -------
    img_array : PIL Image
        The extracted image data
    """

    single_page = WandImage(wand_image.sequence[pagenr])
    single_page.format = 'jpg'
    img_array = np.asarray(bytearray(single_page.make_blob(format="jpg")), dtype=np.uint8)
    img = Image.open(BytesIO(img_array))
    img.load()  # Load the data into the PIL image from the Wand image
    single_page.close()  # Then close the Wand image
    return img
