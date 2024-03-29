import itertools

from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LAParams
from pdfminer.layout import LTFigure
from pdfminer.layout import LTTextBoxHorizontal
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser


def get_problem_page(problem, pdf_path):
    """
    Returns the pdf object belonging to the page of a problem widget

    Parameters
    ----------
    problem : Problem
        Problem object in the database of the currently selected problem
    pdf_path : str
        Path to the PDF file of the exam for this problem

    Returns
    -------
    page : PDFPage
        PDFPage object with information about the current page
    """
    fp = open(pdf_path, "rb")

    parser = PDFParser(fp)
    document = PDFDocument(parser)

    page_number = problem.widget.page
    return next(itertools.islice(PDFPage.create_pages(document), page_number, page_number + 1))


def layout(pdf_page):
    """
    Returns the layout objects in a PDF page

    Parameters
    ----------
    pdf_page : PDFPage
        PDFPage object with information about the current page

    Returns
    -------
    layout : list of pdfminer3 layout objects
        A list of layout objects on the page
    """
    resource_manager = PDFResourceManager()
    la_params = LAParams()
    device = PDFPageAggregator(resource_manager, laparams=la_params)
    interpreter = PDFPageInterpreter(resource_manager, device)
    interpreter.process_page(pdf_page)

    return device.get_result()


def guess_problem_title(problem, pdf_page):
    """
    Tries to find the title of a problem

    Parameters
    ----------
    problem : Problem
        The currently selected problem
    pdf_page : PDFPage
        Information extracted from the PDF page where the problem is located.

    Returns
    -------
    title: str
        The title of the problem, or an empty string if no text is found
    """

    # Get the other problems on the same page
    problems_on_page = [p for p in problem.exam.problems if p.widget.page == problem.widget.page]
    problems_on_page.sort(key=lambda prob: prob.widget.y)

    idx = problems_on_page.index(problem)

    # Determine y coordinates to search for text
    if idx == 0:
        y_above = 0
    else:
        problem_above = problems_on_page[idx - 1]
        y_above = problem_above.widget.y + problem_above.widget.height

    y_current = problem.widget.y + problem.widget.height
    page_height = pdf_page.mediabox[3]

    layout_objects = layout(pdf_page)
    filtered_words = read_lines(layout_objects._objs, y_above, y_current, page_height)

    if not filtered_words:
        return ""

    lines = filtered_words.split("\n")
    return lines[0].strip()


def read_lines(layout_objs, y_top, y_bottom, page_height):
    """
    Returns lines of text from a PDF page within a specified height.

    Parameters
    ----------
    layout_objs : list of layout objects
        The list of objects in the page.
    y_top : double
        Highest top coordinate of each word
    y_bottom : double
        Lowest bottom coordinate of each word
    page_height : int
        Height of the current page in points

    Returns
    -------
    words : str
        The first line of text that if it is found, or else an empty string
    """
    words = []

    # Adapted from https://github.com/euske/pdfminer/issues/171
    #
    # obj.bbox returns the following values: (x0, y0, x1, y1), where
    #
    # x0: the distance from the left of the page to the left edge of the box.
    # y0: the distance from the bottom of the page to the lower edge of the box.
    # x1: the distance from the left of the page to the right edge of the box.
    # y1: the distance from the bottom of the page to the upper edge of the box.

    for obj in layout_objs:
        if isinstance(obj, LTTextBoxHorizontal):
            if y_bottom > page_height - obj.bbox[1] > y_top:
                words.append(obj.get_text())

        elif isinstance(obj, LTFigure):
            words += read_lines(obj._objs, y_top, y_bottom, page_height)

    if not words:
        return ""

    return words[0]
