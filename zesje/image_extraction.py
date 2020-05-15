from io import BytesIO

import numpy as np
import mimetypes
import zipfile

from flask import current_app
from PIL import Image
from pikepdf import Pdf, PdfImage, PdfError
from tempfile import SpooledTemporaryFile
from wand.image import Color, Image as WandImage

EXIF_METHODS = {
    2: Image.FLIP_LEFT_RIGHT,
    3: Image.ROTATE_180,
    4: Image.FLIP_TOP_BOTTOM,
    5: Image.TRANSPOSE,
    6: Image.ROTATE_270,
    7: Image.TRANSVERSE,
    8: Image.ROTATE_90,
}


def extract_images_from_file(file_path_or_buffer, file_info, dpi=300, progress=None):
    """Recursively yield all images from an arbitrary file

    This method supports ZIP, PDF and image files.

    Params
    ------
    file_path_or_buffer : path-like or buffer/stream
        Points to the file to read from
    file_info : str or [str]
        The name of the file, including extension. Is used to determine the mimetype.
    dpi : int
        The resolution to use for flattening PDFs, in DPI
    progress : dict
        Dictionary containing `number` of files extracted and  `total` number of files discovered so far.
        Doesn't need to be passed as an argument, only used for recursion.

    Yields
    ------
    image : PIL.Image or buffer/stream
        The extracted image or the buffer/stream of a non-image file
    file_info : list of str and int
        The hierarchy of the image origin. Contains a combination of the following:
        scan filename, filename in the zip or PDF page number.
        For example: ['scan.zip', 'some_directory_in_zip/student/page.pdf', 3] or ['student-page.png']
    number : int
        The number of files extracted so far.
    total : int
        The number of files discovered so far, not guaranteed to be the final number of files.
    """
    if progress is None:
        progress = dict(number=0, total=0)

    if not isinstance(file_info, list):
        file_info = [file_info]

    mime_type = guess_mimetype(file_info)

    if mime_type is None:
        # Unable to determine mime type, just yield what we currently have
        if len(file_info) == 1:
            progress['total'] += 1

        progress['number'] += 1
        yield file_path_or_buffer, file_info, progress['number'], progress['total']

    elif mime_type in current_app.config['ZIP_MIME_TYPES']:
        with zipfile.ZipFile(file_path_or_buffer, mode='r') as zip_file:
            infolist_files = [zip_info for zip_info in zip_file.infolist() if not zip_info.is_dir()]

            # Count number of non pdf files to update total
            progress['total'] += sum(
                1 for zip_info in infolist_files if guess_mimetype([zip_info.filename]) != 'application/pdf'
            )

            for zip_info in infolist_files:
                with zip_file.open(zip_info, 'r') as zip_info_content:
                    combined_file_info = _combine_file_info(file_info, zip_info.filename)
                    yield from extract_images_from_file(zip_info_content, combined_file_info, dpi, progress)

    elif mime_type == 'application/pdf':
        yield from extract_images_from_pdf(file_path_or_buffer, file_info, dpi, progress)

    elif mime_type.startswith('image/'):
        yield from extract_image_from_image(file_path_or_buffer, file_info, progress)


def extract_image_from_image(file_path_or_buffer, file_info, progress):
    """Yield an image from a file or buffer/stream

    Params
    ------
    file_path_or_buffer : path-like or buffer/stream
        Points to the image file to read from
    file_info : [str]
        The hierarchy of the image origin. See `extract_images_from_file`.
    progress : dict
        Dictionary containing `number` of files extracted and `total` number of files discovered so far.

    Yields
    ------
    Same variables as `extract_images_from_file`.
    """
    if len(file_info) == 1:
        progress['total'] += 1

    progress['number'] += 1
    with Image.open(file_path_or_buffer) as image:
        image = exif_transpose(image)
        image = convert_to_rgb(image)
        yield image, file_info, progress['number'], progress['total']


def extract_images_from_pdf(file_path_or_buffer, file_info=None, dpi=300, progress=None):
    """Yield all images from a PDF file.

    Tries to use PikePDF to extract the images from the given PDF. If PikePDF is not able to extract the image from a
    page, it continues to use Wand to flatten the rest of the pages.

    Params
    ------
    file_path_or_buffer : path-like or buffer/stream
        Points to the image file to read from
    file_info : [str]
        The hierarchy of the image origin. See `extract_images_from_file`.
    dpi : int
        The resolution to use for flattening PDFs, in DPI
    progress : dict
        Dictionary containing `number` of files extracted and  `total` number of files discovered so far.

    Yields
    ------
    Same variables as `extract_images_from_file`.
    """
    if progress is None:
        progress = dict(number=0, total=0)

    if file_info is None:
        file_info = [file_path_or_buffer]

    with Pdf.open(file_path_or_buffer) as pdf_reader:
        progress['total'] += len(pdf_reader.pages)
        use_wand = False

        for page_number, page in enumerate(pdf_reader.pages, start=1):
            if not use_wand:
                try:
                    # Try to use PikePDF, but catch any error it raises
                    img = extract_image_pikepdf(page)

                except (ValueError, AttributeError, PdfError):
                    # Fallback to Wand if extracting with PikePDF failed
                    use_wand = True

            if use_wand:
                img = extract_image_wand(page, dpi)

            img = convert_to_rgb(img)

            progress['number'] += 1
            yield img, _combine_file_info(file_info, 1), progress['number'], progress['total']


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
            with Color('white') as white:
                page_image.background_color = white
                page_image.alpha_channel = 'remove'
                page_image.format = 'jpg'
                img_array = np.asarray(bytearray(page_image.make_blob(format="jpg")), dtype=np.uint8)
                img = Image.open(BytesIO(img_array))
                img.load()  # Load the data into the PIL image from the Wand image

    return img


def convert_to_rgb(img):
    if img.mode in ['L', 'P', 'CMYK', 'HSV']:
        img = img.convert('RGB')
    elif img.mode == 'RGBA':
        # Create a white background, and paste the RGBA image
        # on top of it with the alpha channel as the mask
        background = Image.new('RGB', img.size, (255, 255, 255))
        background.paste(img, mask=img.split()[-1])
        img = background

    return img


def exif_transpose(image):
    """
    If an image has an EXIF Orientation tag, return a new image that is
    transposed accordingly.

    Adapted from PIL.ImageOps.exif_transpose.
    """
    exif = image._getexif()

    if exif is None:
        return image

    orientation = exif.get(0x0112)
    method = EXIF_METHODS.get(orientation)

    return image if not method else image.transpose(method)


def guess_mimetype(file_info):
    """Guess mime type from extension of `file_info` object

    See `extract_images_from_file` for more information on `file_info`.

    Returns
    ------
    mimetype : str or None
        The mimetype if possible to deduce from the extension.
        None otherwise.
    """
    last_filename = _last_filename(file_info)
    if (mimetype := mimetypes.guess_type(last_filename)):
        return mimetype[0]


def readable_filename(file_info):
    """Create a readable file name from a `file_info` object.

    See `extract_images_from_file` for more information on `file_info`.
    """
    return ', '.join(f'page {info}' if type(info) == int else info for info in file_info)


def _combine_file_info(file_info, file_info_to_append):
    return file_info + [file_info_to_append]


def _last_filename(file_info):
    return file_info[-1]
