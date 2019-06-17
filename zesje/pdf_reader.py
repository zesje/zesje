from pdfminer3.converter import PDFPageAggregator
from pdfminer3.layout import LAParams
from pdfminer3.layout import LTFigure
from pdfminer3.layout import LTTextBoxHorizontal
from pdfminer3.pdfdocument import PDFDocument
from pdfminer3.pdfinterp import PDFResourceManager
from pdfminer3.pdfinterp import PDFPageInterpreter
from pdfminer3.pdfpage import PDFPage
from pdfminer3.pdfparser import PDFParser


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
    fp = open(pdf_path, 'rb')

    parser = PDFParser(fp)
    document = PDFDocument(parser)

    # PDFPage.create_pages() only yields a list of key-value pairs
    # So there should be no problem saving the result to a list

    i = 0

    for page in PDFPage.create_pages(document):
        if i == problem.widget.page:
            return page
        i += 1


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
    rsrcmgr = PDFResourceManager()
    laparams = LAParams()
    device = PDFPageAggregator(rsrcmgr, laparams=laparams)
    interpreter = PDFPageInterpreter(rsrcmgr, device)
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

    layout = layout(pdf_page)
    filtered_words = get_words(layout._objs, y_above, y_current, page_height)

    if not filtered_words:
        return ''

    lines = filtered_words[0].split('\n')
    return lines[0].strip()


def get_words(layout_objs, y_top, y_bottom, page_height):
    """
    Returns the text from a pdf page within a specified height.

    Parameters
    ----------
    page_height : int
        Height of the current page in points
    layout_objs : list of layout objects
        The list of objects in the page.
    y_top : double
        Highest top coordinate of each word
    y_bottom : double
        Lowest bottom coordinate of each word

    Returns
    -------
    words : list of tuples
        A list of tuples with the (y, text) values.
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
            words += get_words(obj._objs, y_top, y_bottom, page_height)

    return words
