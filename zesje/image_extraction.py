from io import BytesIO

import numpy as np
import mimetypes
import zipfile
import re

from flask import current_app
from PIL import Image
from pikepdf import Pdf, PdfImage, PdfError
from tempfile import SpooledTemporaryFile
from wand.image import Color, Image as WandImage

from .database import Student
from .constants import ID_GRID_DIGITS

EXIF_METHODS = {
    2: Image.FLIP_LEFT_RIGHT,
    3: Image.ROTATE_180,
    4: Image.FLIP_TOP_BOTTOM,
    5: Image.TRANSPOSE,
    6: Image.ROTATE_270,
    7: Image.TRANSVERSE,
    8: Image.ROTATE_90,
}

RE_STUDENT_AT_LEAST = re.compile(
    fr'(?P<student_id>\d{{{ID_GRID_DIGITS}}})(\D)*?(-(?P<page>\d{{1,2}}))?(-(?P<copy>\d{{1,2}}))?(\.(?P<ext>\w+))?$'
)
RE_PAGE_AT_LEAST = re.compile(
    r'(^|.*?\D+)(?P<page>\d{1,2})(\D+?|$)((?P<copy>\d{1,2}))?(\.(?P<ext>\w+))?$'
)
RE_COPY = re.compile(
    r'^(\D*(?P<copy>\d{1,2})\D*?)(\.(?P<ext>\w+))?$'
)
RE_ANY_NUMBER = re.compile(
    r'(^|\D+)\d{1,2}($|\D+)'
)


def extract_pages_from_file(file_path_or_buffer, file_info, dpi=300):
    """Recursively yield all images with page info from an arbitrary file

    This method supports ZIP, PDF and image files.

    Params
    ------
    file_path_or_buffer : path-like or buffer/stream
        Points to the file to read from
    file_info : str or [str]
        The name of the file, including extension. Is used to determine the mimetype.
    dpi : int
        The resolution to use for flattening PDFs, in DPI

    Yields
    ------
    image : PIL.Image or buffer/stream
        The extracted image or the buffer/stream of a non-image file
    page_info : tuple of (int or None)
        Contains (student_id, page_number, copy_number). All can be None.
    file_info : list of str
        The hierarchy of the file origin. Contains a combination of the following:
        scan filename, filename in the zip or PDF page number.
        For example: ['scan.zip', 'some_directory_in_zip/student/page.pdf', 3] or ['student-page.png']
    number : int
        The number of files extracted so far.
    total : int
        The total number of file to extract
    """
    file_infos = list(extract_images_or_infos_from_file(file_path_or_buffer, file_info, dpi, only_info=True))
    final_total = len(file_infos)

    students = Student.query.all()
    page_infos = [guess_page_info(info, students) for info in file_infos]

    page_infos = guess_missing_page_info(page_infos)

    for number, (page_info, (image, file_info)) in enumerate(zip(
        page_infos,
        extract_images_or_infos_from_file(file_path_or_buffer, file_info, dpi, only_info=False)
    ), start=1):
        yield image, page_info, file_info, number, final_total


def extract_images_or_infos_from_file(file_path_or_buffer, file_info, dpi=300, only_info=False):
    """Extract images or file tree info from an arbitrary file

    Params
    ------
    file_path_or_buffer : path-like or buffer/stream
        Points to the file to read from
    file_info : str or [str]
        The name of the file, including extension. Is used to determine the mimetype.
        Also see `file_info` in yields for this function.
    dpi : int
        The resolution to use for flattening PDFs, in DPI
    only_info : bool
        When `False`, yield everything. When `True`, only yield file tree info.

    Yields
    ------
    image : PIL.Image or buffer/stream
        The extracted image or the buffer/stream of a non-image file
    file_info : list of str and int
        The hierarchy of the file origin. Contains a combination of the following:
        scan filename, filename in the zip or PDF page number.
        For example: ['scan.zip', 'some_directory_in_zip/student/page.pdf', 3] or ['student-page.png']
        When `only_info` is `True`, this is the only parameter that is yielded.
    """
    if not isinstance(file_info, list):
        file_info = [file_info]

    mime_type = guess_mimetype(file_info)

    if mime_type is None:
        yield from _extract_from_unknown(file_path_or_buffer, file_info, only_info)
    elif mime_type in current_app.config['ZIP_MIME_TYPES']:
        with zipfile.ZipFile(file_path_or_buffer, mode='r') as zip_file:
            infolist_files = (zip_info for zip_info in zip_file.infolist() if not zip_info.is_dir())

            for zip_info in infolist_files:
                with zip_file.open(zip_info, 'r') as zip_info_content:
                    combined_file_info = _combine_file_info(file_info, zip_info.filename)
                    yield from extract_images_or_infos_from_file(
                        zip_info_content, combined_file_info, dpi, only_info=only_info)

    elif mime_type == 'application/pdf':
        yield from extract_images_from_pdf(file_path_or_buffer, file_info, dpi, only_info=only_info)

    elif mime_type.startswith('image/'):
        yield from extract_image_from_image(file_path_or_buffer, file_info, only_info=only_info)
    else:
        yield from _extract_from_unknown(file_path_or_buffer, file_info, only_info)


def _extract_from_unknown(file_path_or_buffer, file_info, only_info=False):
    """Helper function to yield a file of unknown type

    Params
    ------
    Same as `extract_image_from_image`

    Yields
    ------
    Same as `extract_images_or_infos_from_file`
    """
    if not only_info:
        # No images in here, just yield what we currently have
        yield file_path_or_buffer, file_info

    else:
        # We yield no info for files that are not images.
        # This ensures they are not included when checking for ambiguities.
        yield []


def extract_image_from_image(file_path_or_buffer, file_info, only_info=False):
    """Yield an image from a file or buffer/stream

    Params
    ------
    file_path_or_buffer : path-like or buffer/stream
        Points to the image file to read from
    file_info : [str]
        The hierarchy of the image origin. See `extract_pages_from_file`.

    Yields
    ------
    Same as `extract_images_or_infos_from_file`.
    """
    if not only_info:
        with Image.open(file_path_or_buffer) as image:
            image = exif_transpose(image)
            image = convert_to_rgb(image)
            yield image, file_info
    else:
        yield file_info


def extract_images_from_pdf(file_path_or_buffer, file_info=None, dpi=300, only_info=False):
    """Yield all images from a PDF file.

    Tries to use PikePDF to extract the images from the given PDF. If PikePDF is not able to extract the image from a
    page, it continues to use Wand to flatten the rest of the pages.

    Params
    ------
    file_path_or_buffer : path-like or buffer/stream
        Points to the image file to read from
    file_info : [str]
        The hierarchy of the image origin. See `extract_pages_from_file`.
    dpi : int
        The resolution to use for flattening PDFs, in DPI

    Yields
    ------
    Same as `extract_images_or_infos_from_file`.
    """
    if file_info is None:
        file_info = []

    with Pdf.open(file_path_or_buffer) as pdf_reader:
        number_of_pages = len(pdf_reader.pages)
        use_wand = False

        for page_number, page in enumerate(pdf_reader.pages, start=1):
            # Only include page number in file_info if there are multiple pages
            if number_of_pages > 1:
                file_info_page = _combine_file_info(file_info, page_number)
            else:
                file_info_page = file_info

            if not only_info:
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
                yield img, file_info_page
            else:
                yield file_info_page


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


def guess_missing_page_info(page_infos):
    """Guesses any missing page and copy numbers

    Sets all unknown pages to 0 and all unknown copies to 1.

    If a duplicate pair of (page, copy) is detected for a student after guessing,
    we have an ambiguity, thus set all pages and copies to None for that student.

    Params
    ------
    page_infos : tuple of (None or int)
        Contains (student_id, page, copy). All can be None.
        Page is 0-indexed, copy is 1-indexed.

    Returns
    -------
    page_infos : tuple of (None or int)
        Same as param `page_infos`, but including guessed info.
    """
    page_info_per_student = {}
    for index, page_info in enumerate(page_infos):
        student_id, page, copy = page_info
        if student_id is None:
            continue

        student_page_info = page_info_per_student.get(student_id, [])
        page_info_per_student[student_id] = student_page_info + [(index, page_info)]

    for student_id, student_page_infos in page_info_per_student.items():
        # Set all unknown pages to 0, unknown copies to 0
        for local_index, (index, (_, page, copy)) in enumerate(student_page_infos):
            if None in (page, copy):
                page = page if page is not None else 0
                copy = copy if copy is not None else 1
                student_page_infos[local_index] = (index, (student_id, page, copy))

        page_copies = [(page, copy) for (_, (_, page, copy)) in student_page_infos]

        # If we have duplicates, set all to None
        if len(page_copies) != len(set(page_copies)):
            for index, _ in student_page_infos:
                page_infos[index] = (student_id, None, None)

        # Otherwise update the page infos with the guessed info
        else:
            for index, page_info in student_page_infos:
                page_infos[index] = page_info

    return page_infos


def guess_page_info(file_info, students):
    """Guess information about student, copy and page from the file name.

    Supports the following formats:
    - File of format student-page(-copy).ext
    - Any file tree containing student (name or number), page or copy (in order)

    Note that the page number in a PDF is also part of the file tree.

    Params
    ------
    file_info : list of str and int
        See `image_extraction._extract_images_or_infos_from_file`.
    students : list of Student
        Students to consider for detecting names

    Returns
    ------
    student_id : int or None
        Student number
    page : int or None
        Page number, 0-indexed
    copy : int or None
        Copy number, 1-indexed
    """
    student_id, page, copy = None, None, None
    file_info_folders = sum((str(info).split('/') for info in file_info), [])
    for current_info in file_info_folders:
        # Check each time if we find a student number
        # This is to ensure the second student number in the path
        # is not misinterpreted as page or copy number.
        if (match := RE_STUDENT_AT_LEAST.match(current_info)):
            if student_id is not None and int(match.group('student_id')) != student_id:
                student_id, page, copy = None, None, None
                break
            else:
                student_id = int(match.group('student_id'))
                page = int(match.group('page')) - 1 if match.group('page') else None
                copy = int(match.group('copy')) if match.group('copy') else None

        elif student_id is None:
            matched_students_names = [
                student for student in students
                if ((student.first_name + ' ' + student.last_name) in current_info)
            ]
            if len(matched_students_names) > 1:
                break
            elif len(matched_students_names) == 1:
                student_id = matched_students_names[0].id

        elif page is None:
            if (match := RE_PAGE_AT_LEAST.match(current_info)):
                page = int(match.group('page')) - 1
                copy = int(match.group('copy')) if match.group('copy') else None
        elif copy is None:
            if (match := RE_COPY.match(current_info)):
                copy = int(match.group('copy'))
        else:
            if RE_ANY_NUMBER.search(current_info):
                # Return the student number to trigger a page/copy ambiguity
                page = None
                copy = None

    return student_id, page, copy


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
