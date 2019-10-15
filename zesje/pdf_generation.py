from tempfile import NamedTemporaryFile

import PIL
import shutil
import os
from pdfrw import PdfReader, PdfWriter, PageMerge
from pylibdmtx.pylibdmtx import encode
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas


output_pdf_filename_format = '{0:05d}.pdf'

# the size of the markers in points
MARKER_FORMAT = {
    "margin": 10 * mm,
    "marker_line_length": 8 * mm,
    "marker_line_width": 1 * mm,
    "bar_length": 40 * mm
}

# the parameters of drawing checkboxes
CHECKBOX_FORMAT = {
    "margin": 5,
    "font_size": 11,
    "box_size": 9
}
PAGE_FORMATS = {
    "A4": (595.276, 841.89),
    "US letter": (612, 792),
}


def generate_pdfs(exam_pdf_file, copy_nums, output_paths, exam_token=None, id_grid_x=0,
                  id_grid_y=0, datamatrix_x=0, datamatrix_y=0, cb_data=None):
    """
    Generates an overlay onto the exam PDF file and saves it at the output path.

    Can be used to generate either a generic overlay (corner markers and student grid)
    or a copy specific overlay (datamatrix and copy number), depending on copy_nums

    To ensure the page information fits into the datamatrix grid, adhere to
    (# of letters in exam ID) + 2 * (# of digits in exam ID) = C for a certain
    constant C. The reason for this is that libdmtx encodes two digits in as
    much space as one letter.

    If maximum interchangeability with version 1 QR codes is desired (error
    correction level M), use exam IDs composed of only uppercase letters, and
    composed of at most 12 letters.
    Parameters
    ----------
    exam_pdf_file : file object or str
        The exam PDF file or its filename
    exam_token : str
        The identifier of the exam
    copy_nums : [int | None]
        Copy numbers of the generated pdfs. These are integers greater than 1
        If None is given, the generic part of the overlay is generated.
        If an integer is given, only copy specific parts are generated.
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
    cb_data : list[ (int, int, int, str)]
        The data needed for drawing a checkbox, namely: the x coordinate; y coordinate; page number and label

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
            if copy_num is None:
                # Draw corner markers and student id grid
                _generate_generic_overlay(overlay_canv, pagesize, len(exam_pdf.pages),
                                          id_grid_x, id_grid_y, cb_data)
            else:
                # Draw the datamatric and copy number
                _generate_copy_overlay(overlay_canv, pagesize, exam_token, copy_num,
                                       len(exam_pdf.pages), datamatrix_x, datamatrix_y)
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


def write_finalized_exam(exam_dir, exam_pdf_file, id_grid_x, id_grid_y, cb_data=None):
    original_pdf_file = os.path.join(exam_dir, 'original.pdf')
    shutil.move(exam_pdf_file, original_pdf_file)

    generate_pdfs(
        exam_pdf_file=original_pdf_file,
        exam_token=None,
        copy_nums=[None],
        output_paths=[exam_pdf_file],
        id_grid_x=id_grid_x,
        id_grid_y=id_grid_y,
        cb_data=cb_data
    )

    os.remove(original_pdf_file)


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


def add_checkbox(canvas, x, y, label):
    """
    draw a checkbox and draw a single character on top of the checkbox

    Parameters
    ----------
    canvas : reportlab canvas object

    x : int
        the x coordinate of the top left corner of the box in points (pt)
    y : int
        the y coordinate of the top left corner of the box in points (pt)
    label: str
        A string representing the label that is drawn on top of the box, will only take the first character

    """
    x_label = x + 1  # location of the label
    y_label = y + CHECKBOX_FORMAT["margin"]  # remove fontsize from the y label since we draw from the bottom left up
    box_y = y - CHECKBOX_FORMAT["box_size"]  # remove the markboxsize because the y is the coord of the top
    # and reportlab prints from the bottom

    # check that there is a label to print
    if (label and not (len(label) == 0)):
        canvas.setFont('Helvetica', CHECKBOX_FORMAT["font_size"])
        canvas.drawString(x_label, y_label, label[0])

    canvas.rect(x, box_y, CHECKBOX_FORMAT["box_size"], CHECKBOX_FORMAT["box_size"])


def generate_datamatrix(exam_token, page_num, copy_num):
    """
    Generates a DataMatrix code to be used on a page.

    To ensure the page information fits into the datamatrix grid, adhere to
    (# of letters in exam ID) + 2 * (# of digits in exam ID) = C for a certain
    constant C. The reason for this is that pylibdmtx encodes two digits in as
    much space as one letter.

    If maximum interchangeability with version 1 QR codes is desired (error
    correction level M), use exam IDs composed of only uppercase letters, and
    composed of at most 12 letters.

    Parameters
    ----------
    exam_token : str
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

    data = f'{exam_token}/{copy_num:04d}/{page_num:02d}'

    encoded = encode(data.encode('utf-8'), size='18x18')
    datamatrix = PIL.Image.frombytes('RGB', (encoded.width, encoded.height), encoded.pixels)
    datamatrix = datamatrix.resize((44, 44)).convert('L')
    return datamatrix


def _generate_generic_overlay(canv, pagesize, num_pages, id_grid_x, id_grid_y, cb_data=None):
    """
    Generates generic overlay PDF, which can then be overlaid onto
    the exam PDF. Only generates non copy specific data.

    Parameters
    ----------
    canv : ReportLab Canvas object
        The empty ReportLab canvas on which the overlay should be generated
    pagesize : (float, float)
        The ReportLab-style (i.e. (width, height)) page size of the canvas
    copy_num : int
        The copy number for which the overlay is being generated.
        The datamatrix is not generated when this is None.
    num_pages : int
        The amount of pages that the generated overlay should count
    id_grid_x : int
        The x coordinate where the student ID grid should be placed
    id_grid_y : int
        The y coordinate where the student ID grid should be placed
    cb_data : list[ (int, int, int, str)]
        The data needed for drawing a checkbox, namely: the x coordinate; y coordinate; page number and label
    """
    # transform y-cooridate to different origin location
    id_grid_y = pagesize[1] - id_grid_y

    # ID grid on first page only
    generate_id_grid(canv, id_grid_x, id_grid_y)

    # create index for list of checkbox data and sort the data on page
    if cb_data:
        index = 0
        max_index = len(cb_data)
        cb_data = sorted(cb_data, key=lambda tup: tup[2])
        # invert the y axis
        cb_data = [(cb[0], pagesize[1] - cb[1], cb[2], cb[3]) for cb in cb_data]
    else:
        index = 0
        max_index = 0

    for page_num in range(num_pages):
        _add_corner_markers_and_bottom_bar(canv, pagesize)

        # call generate for all checkboxes that belong to the current page
        while index < max_index and cb_data[index][2] <= page_num:
            x, y, _, label = cb_data[index]
            add_checkbox(canv, x, y, label)
            index += 1

        canv.showPage()


def _generate_copy_overlay(canv, pagesize, exam_token, copy_num, num_pages, datamatrix_x, datamatrix_y):
    """
    Generates an overlay ('watermark') PDF, which can then be overlaid onto
    the exam PDF. Only generates copy specific data.

    To ensure the page information fits into the datamatrix grid in the overlay,
    adhere to (# of letters in exam ID) + 2 * (# of digits in exam ID) = C for
    a certain constant C. The reason for this is that pylibdmtx encodes two
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
    exam_token : str
        The identifier of the exam
    copy_num : int
        The copy number for which the overlay is being generated.
    num_pages : int
        The amount of pages that the generated overlay should count
    datamatrix_x : int
        The x coordinate where the DataMatrix codes should be placed
    datamatrix_y : int
        The y coordinate where the DataMatrix codes should be placed
    """
    # Font settings for the copy number (printed under the datamatrix)
    fontsize = 12
    canv.setFont('Helvetica', fontsize)

    for page_num in range(num_pages):
        datamatrix = generate_datamatrix(exam_token, page_num, copy_num)

        # transform y-cooridate to different origin location
        datamatrix_y_adjusted = pagesize[1] - datamatrix_y - datamatrix.height

        canv.drawInlineImage(datamatrix, datamatrix_x, datamatrix_y_adjusted)
        canv.drawString(
            datamatrix_x, datamatrix_y_adjusted - (fontsize * 0.66),
            f" # {copy_num}"
        )

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
    marker_line_length = MARKER_FORMAT["marker_line_length"]
    bar_length = MARKER_FORMAT["bar_length"]

    # Calculate coordinates offset from page edge
    left = MARKER_FORMAT["margin"]
    bottom = MARKER_FORMAT["margin"]
    right = page_width - MARKER_FORMAT["margin"]
    top = page_height - MARKER_FORMAT["margin"]

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


def page_is_size(exam_pdf_file, shape, tolerance=0):
    """
    Verify whether all pages of the file have the same shape and return it.

    Parameters
    ----------
    exam_pdf_file : file object or str
        The exam PDF file or its filename.
    shape : pair of floats
        Desired page shape in points.
    tolerance : float
        Relative tolerance to size differences.

    Returns
    -------
    valid : bool
        If the pdf matches the page sizes

    Raises
    ------
    ValueError
        If the pages have different sizes.
    """
    exam_pdf = PdfReader(exam_pdf_file)
    tol = (shape[0] * tolerance, shape[1] * tolerance)

    def page_is_bad(page):
        return (abs(float(page.MediaBox[2]) - shape[0]) > tol[0]
                or abs(float(page.MediaBox[3]) - shape[1]) > tol[1])

    invalid = any(page_is_bad(p) for p in exam_pdf.pages)

    # Be considerate and return the caret in the stream to the beginning.
    try:
        exam_pdf_file.seek(0)
    except Exception:
        # Not a file
        pass

    return not invalid


def save_with_even_pages(pdf_path, exam_pdf_file):
    exam_pdf = PdfReader(exam_pdf_file)
    pagecount = len(exam_pdf.pages)

    if (pagecount % 2 == 0):
        exam_pdf_file.seek(0)
        exam_pdf_file.save(pdf_path)
        return

    new = PdfWriter()
    new.addpages(exam_pdf.pages)
    blank = PageMerge()
    box = exam_pdf.pages[0].MediaBox
    blank.mbox = box
    blank = blank.render()
    new.addpage(blank)

    new.write(pdf_path)
