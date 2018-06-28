from io import BytesIO
from tempfile import NamedTemporaryFile

import PIL
from pdfrw import PdfReader, PdfWriter, PageMerge
from pystrich.datamatrix import DataMatrixEncoder
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas


output_pdf_filename_format = '{0:05d}.pdf'


def generate_pdfs(exam_pdf_file, exam_id, copy_nums, output_paths, id_grid_x,
                  id_grid_y, datamatrix_x, datamatrix_y):
    """
    Generate the final PDFs from the original exam PDF.

    To maintain a consistent size of the DataMatrix codes, adhere to (# of
    letters in exam ID) + 2 * (# of digits in exam ID) = C for a certain
    constant C. The reason for this is that pyStrich encodes two digits in as
    much space as one letter.

    If maximum interchangeability with version 1 QR codes is desired (error
    correction level M), use exam IDs composed of only uppercase letters, and
    composed of at most 12 letters.

    Parameters
    ----------
    exam_pdf_file : file object or str
        The exam PDF file or its filename
    exam_id : str
        The identifier of the exam
    copy_nums : [int]
        copy numbers of the generated pdfs. These are integers greater than 1
    output_paths : [str]
        Output file paths of the generated pdfs
    id_grid_x : int
        The x coordinate where the student ID grid should be placed
    id_grid_y : int
        The y coordinate where the student ID grid should be placed
    datamatrix_x : int
        The x coordinate where the DataMatrix code should be placed
    datamatrix_y : int
        The y coordinate where the DataMatrix code should be placed
    """
    exam_pdf = PdfReader(exam_pdf_file)
    mediabox = exam_pdf.pages[0].MediaBox
    pagesize = (float(mediabox[2]), float(mediabox[3]))

    for copy_num, output_path in zip(copy_nums, output_paths):
        # ReportLab can't deal with file handles, but only with file names,
        # so we have to use a named file
        with NamedTemporaryFile() as overlay_file:
            # Generate overlay
            overlay_canv = canvas.Canvas(overlay_file.name, pagesize=pagesize)
            _generate_overlay(overlay_canv, pagesize, exam_id, copy_num,
                              len(exam_pdf.pages), id_grid_x, id_grid_y,
                              datamatrix_x, datamatrix_y)
            overlay_canv.save()

            # Merge overlay and exam
            try:
                exam_pdf_file.seek(0)  # go back to the start of the file object
            except AttributeError:
                # exam_pdf_file is the filename instead of the file object, so we don't have to seek to the start of it
                pass

            exam_pdf = PdfReader(exam_pdf_file)
            overlay_pdf = PdfReader(overlay_file)

            for page_idx, exam_page in enumerate(exam_pdf.pages):
                # First prepare the overlay merge, and then add it to the exam merge.
                # It might seem more efficient to do it the other way around, because then we only need to load the exam
                # PDF once. However, if there are elements in the exam PDF at the same place as the overlay, that would
                # mean that the overlay ends up on the bottom, which is not good.
                overlay_merge = PageMerge().add(overlay_pdf.pages[page_idx])[0]
                exam_merge = PageMerge(exam_page).add(overlay_merge)
                exam_merge.render()

            PdfWriter(output_path, trailer=exam_pdf).write()


def join_pdfs(output_filename, pdf_paths):
    """
    Join all the final PDFs into a single big PDF.

    Parameters
    ----------
    output_filename : str
        The filename where the joined PDF file should be stored
    pdf_paths : [str]
        The paths of the PDF files that should be joined
    """
    writer = PdfWriter()

    for path in pdf_paths:
        writer.addpages(PdfReader(path).pages)

    writer.write(output_filename)


def generate_id_grid(canv, x, y):
    """
    Generates the student ID grid on the given canvas at the given coordinates.

    Parameters
    ----------
    canv : ReportLab Canvas object
        The ReportLab canvas on which the grid should be drawn
    x : int
        The x coordinate where the grid should be drawn
    x : int
        The y coordinate where the grid should be drawn
    """

    fontsize = 11  # Size of font
    margin = 5  # Margin between elements and sides
    markboxsize = fontsize - 2  # Size of student number boxes
    textboxwidth = fontsize * 15  # Width of textbox
    textboxheight = markboxsize * 2 + margin + 2  # Height of textbox
    digits = 7  # Max amount of digits you want for student numbers

    canv.setFont('Helvetica', fontsize)

    # Draw numbers and boxes for student number
    canv.drawString(x + margin, y - fontsize - margin, "Student number :")
    for i in range(10):
        canv.drawString(x + margin,
                        y - ((i + 2) * (fontsize + margin)),
                        str(i))
        for j in range(digits):
            canv.rect(x + (j + 1) * (fontsize + margin),
                      y - (i + 2) * (fontsize + margin) - 1,
                      markboxsize, markboxsize)

    # Draw first name text and box
    canv.drawString(x + (digits + 1) * (fontsize + margin) + 3 * margin - 1,
                    y - fontsize - margin, "First name :")

    canv.rect(x + (digits + 1) * (fontsize + margin) + 3 * margin,
              y - fontsize * 3 - 3 * margin - 1,
              textboxwidth, textboxheight)

    # Draw last name text and box
    canv.drawString(x + (digits + 1) * (fontsize + margin) + 3 * margin - 1,
                    y - 5 * fontsize - 2 * margin, "Last name :")

    canv.rect(x + (digits + 1) * (fontsize + margin) + 3 * margin,
              y - fontsize * 6 - 6 * margin - 1,
              textboxwidth, textboxheight)


def generate_datamatrix(exam_id, page_num, copy_num):
    """
    Generates a DataMatrix code to be used on a page.

    To maintain a consistent size of the DataMatrix codes, adhere to (# of
    letters in exam ID) + 2 * (# of digits in exam ID) = C for a certain
    constant C. The reason for this is that pyStrich encodes two digits in as
    much space as one letter.

    If maximum interchangeability with version 1 QR codes is desired (error
    correction level M), use exam IDs composed of only uppercase letters, and
    composed of at most 12 letters.

    Parameters
    ----------
    exam_id : str
        The identifier of the exam
    page_num : int
        The page number
    copy_num : int
        The number of the copy

    Returns
    -------
    Pillow Image object
        The Pillow image of the DataMatrix code, including quiet zone (you
        don't need to add a quiet zone yourself)
    """

    data = f'{exam_id}/{copy_num:04d}/{page_num:02d}'

    image_bytes = DataMatrixEncoder(data).get_imagedata(cellsize=2)
    return PIL.Image.open(BytesIO(image_bytes))


def _generate_overlay(canv, pagesize, exam_id, copy_num, num_pages, id_grid_x,
                      id_grid_y, datamatrix_x, datamatrix_y):
    """
    Generates an overlay ('watermark') PDF, which can then be overlaid onto
    the exam PDF.

    To maintain a consistent size of the DataMatrix codes in the overlay,
    adhere to (# of letters in exam ID) + 2 * (# of digits in exam ID) = C for
    a certain constant C. The reason for this is that pyStrich encodes two
    digits in as much space as one letter.

    If maximum interchangeability with version 1 QR codes is desired (error
    correction level M), use exam IDs composed of only uppercase letters, and
    composed of at most 12 letters.

    Parameters
    ----------
    canv : ReportLab Canvas object
        The empty ReportLab canvas on which the overlay should be generated
    pagesize : (float, float)
        The ReportLab-style (i.e. (width, height)) page size of the canvas
    exam_id : str
        The identifier of the exam
    copy_num : int
        The copy number for which the overlay is being generated
    num_pages : int
        The amount of pages that the generated overlay should count
    id_grid_x : int
        The x coordinate where the student ID grid should be placed
    id_grid_y : int
        The y coordinate where the student ID grid should be placed
    datamatrix_x : int
        The x coordinate where the DataMatrix codes should be placed
    datamatrix_y : int
        The y coordinate where the DataMatrix codes should be placed
    """

    # transform y-cooridate to different origin location
    id_grid_y = pagesize[1] - id_grid_y

    # ID grid on first page only
    generate_id_grid(canv, id_grid_x, id_grid_y)

    for page_num in range(num_pages):
        _add_corner_markers_and_bottom_bar(canv, pagesize)

        datamatrix = generate_datamatrix(exam_id, page_num, copy_num)

        # transform y-cooridate to different origin location
        datamatrix_y_adjusted = pagesize[1] - datamatrix_y - datamatrix.height

        canv.drawInlineImage(datamatrix, datamatrix_x, datamatrix_y_adjusted)

        canv.showPage()


def _add_corner_markers_and_bottom_bar(canv, pagesize):
    """
    Adds corner markers and a bottom bar to the given canvas.

    Parameters
    ----------
    canv : ReportLab Canvas object
        The canvas on which the corner markers and bottom bar should be drawn. Corner markers
        will only be drawn on the current page of the canvas.
    pagesize : (float, float)
        The ReportLab-style (i.e. (width, height)) page size of the canvas
    """
    page_width = pagesize[0]
    page_height = pagesize[1]
    margin = 10 * mm
    marker_line_length = 8 * mm
    bar_length = 40 * mm

    # Calculate coordinates offset from page edge
    left = margin
    bottom = margin
    right = page_width - margin
    top = page_height - margin

    # Calculate start and end coordinates of bottom bar
    bar_start = page_width / 2 - bar_length / 2
    bar_end = page_width / 2 + bar_length / 2

    canv.lines([
        # Bottom left corner marker
        (left, bottom, left + marker_line_length, bottom),
        (left, bottom, left, bottom + marker_line_length),
        # Bottom right corner marker
        (right, bottom, right - marker_line_length, bottom),
        (right, bottom, right, bottom + marker_line_length),
        # Top right corner marker
        (right, top, right - marker_line_length, top),
        (right, top, right, top - marker_line_length),
        # Top left corner marker
        (left, top, left + marker_line_length, top),
        (left, top, left, top - marker_line_length),
        # Bottom bar
        (bar_start, bottom, bar_end, bottom)
    ])


def page_size(exam_pdf_file):
    """
    Verify whether all pages of the file have the same shape and return it.

    Parameters
    ----------
    exam_pdf_file : file object or str
        The exam PDF file or its filename.

    Returns
    -------
    shape : tuple of floats
        Page width and height in points.

    Raises
    ------
    ValueError
        If the pages have different sizes.
    """
    exam_pdf = PdfReader(exam_pdf_file)
    mediabox = exam_pdf.pages[0].MediaBox
    shape = (float(mediabox[2]), float(mediabox[3]))
    for page in exam_pdf.pages:
        if (float(page.MediaBox[2]), float(page.MediaBox[3])) != shape:
            raise ValueError('Exam pages have different sizes.')

    # Be considerate and return the caret in the stream to the beginning.
    try:
        exam_pdf_file.seek(0)
    except Exception:
        # Not a file
        pass

    return shape