import os
from io import BytesIO
from tempfile import NamedTemporaryFile

import PIL
from pdfrw import PdfReader, PdfWriter, PageMerge
from pystrich.datamatrix import DataMatrixEncoder
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas


_output_pdf_filename_format = '{0:05d}.pdf'


def generate_pdfs(exam_pdf_file, exam_id, output_dir, num_copies, id_grid_x,
                  id_grid_y, datamatrix_x, datamatrix_y):
    """
    Generate the final PDFs from the original exam PDF.

    Parameters
    ----------
    TODO
    """
    exam_pdf = PdfReader(exam_pdf_file)

    mediabox = exam_pdf.pages[0].MediaBox
    pagesize = (float(mediabox[2]), float(mediabox[3]))

    for copy_idx in range(num_copies):
        # ReportLab can't deal with file handles, but only with file names,
        # so we have to use a named file
        with NamedTemporaryFile() as overlay_file:
            # Generate overlay
            overlay_canv = canvas.Canvas(overlay_file.name, pagesize=pagesize)
            _generate_overlay(overlay_canv, pagesize, exam_id, copy_idx,
                              len(exam_pdf.pages), id_grid_x, id_grid_y,
                              datamatrix_x, datamatrix_y)
            overlay_canv.save()

            # Merge overlay and exam
            overlay_pdf = PdfReader(overlay_file)
            for page_idx, exam_page in enumerate(exam_pdf.pages):
                # First prepare the exam merge, and then add it to the overlay.
                # If it were the other way around, all the overlays would
                # 'stick' to the exam.
                exam_merge = PageMerge().add(exam_page)[0]
                overlay_merge = PageMerge(overlay_pdf.pages[page_idx]) \
                    .add(exam_merge)
                overlay_merge.render()
            path = os.path.join(output_dir,
                                _output_pdf_filename_format.format(copy_idx))
            PdfWriter(path, trailer=overlay_pdf).write()


def join_pdfs(directory, output_file, num_copies):
    """
    Join all the final PDFs into a single big PDF.

    Parameters
    ----------
    TODO
    """
    writer = PdfWriter()

    for copy_idx in range(num_copies):
        path = os.path.join(directory,
                            _output_pdf_filename_format.format(copy_idx))
        writer.addpages(PdfReader(path).pages)

    writer.write(output_file)


def generate_id_grid(canv, x, y):
    """
    Generates the student ID grid on the given canvas at the given coordinates.

    Parameters
    ----------
    TODO
    """
    canv.setFont('Helvetica', 14)
    canv.drawString(x * mm, y * mm, 'Beautiful ID Grid')


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
    PIL.Image.Image object
        The PIL image of the DataMatrix code, including quiet zone (you don't
        need to add a quiet zone yourself)
    """

    data = f'{exam_id}/{copy_num:04d}/{page_num:02d}'

    image_bytes = DataMatrixEncoder(data).get_imagedata(cellsize=2)
    return PIL.Image.open(BytesIO(image_bytes))


def _generate_overlay(canv, pagesize, exam_id, copy_num, num_pages, id_grid_x,
                      id_grid_y, datamatrix_x, datamatrix_y):
    """
    Generates an overlay ('watermark') PDF, which can then be overlaid onto
    the exam PDF.

    Parameters
    ----------
    TODO
    """
    # ID grid on first page only
    generate_id_grid(canv, id_grid_x, id_grid_y)

    for page_num in range(num_pages):
        _add_corner_markers(canv, pagesize)

        datamatrix = generate_datamatrix(exam_id, page_num, copy_num)
        canv.drawInlineImage(datamatrix, datamatrix_x * mm, datamatrix_y * mm)

        canv.showPage()


def _add_corner_markers(canv, pagesize, margin=10):
    """
    Adds corner markers to the given canvas.

    Parameters
    ----------
    TODO
    """
    width = pagesize[0]
    height = pagesize[1]
    length = 8 * mm  # length of the lines

    # Calculate coordinates offset from page edge
    left = margin * mm
    bottom = margin * mm
    right = width - margin * mm
    top = height - margin * mm

    canv.lines([
        # Bottom left
        (left, bottom, left + length, bottom),
        (left, bottom, left, bottom + length),
        # Bottom right
        (right, bottom, right - length, bottom),
        (right, bottom, right, bottom + length),
        # Top right
        (right, top, right - length, top),
        (right, top, right, top - length),
        # Top left
        (left, top, left + length, top),
        (left, top, left, top - length)
    ])
