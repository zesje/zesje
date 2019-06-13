import os

import pdfminer3

from pdfminer3.converter import PDFPageAggregator
from pdfminer3.layout import LAParams
from pdfminer3.pdfdocument import PDFDocument
from pdfminer3.pdfinterp import PDFResourceManager
from pdfminer3.pdfinterp import PDFPageInterpreter
from pdfminer3.pdfpage import PDFPage
from pdfminer3.pdfparser import PDFParser

from .api.exams import PAGE_FORMATS


def get_problem_title(problem, app_config):
    """
    Returns the title of a problem

    Parameters
    ----------
    app_config : dict
        Configuration of the app
    problem : Problem
        The currently selected problem

    Returns
    -------
    title: str
        The title of the problem, or an empty string if no text is found
    """
    data_dir = app_config.get('DATA_DIRECTORY', 'data')
    pdf_path = os.path.join(data_dir, f'{problem.exam_id}_data', 'exam.pdf')

    fp = open(pdf_path, 'rb')

    parser = PDFParser(fp)
    document = PDFDocument(parser)
    rsrcmgr = PDFResourceManager()
    laparams = LAParams()
    device = PDFPageAggregator(rsrcmgr, laparams=laparams)
    interpreter = PDFPageInterpreter(rsrcmgr, device)

    # Get the other problems on the same page
    problems_on_page = [p for p in problem.exam.problems if p.widget.page == problem.widget.page]
    problems_on_page.sort(key=lambda prob: prob.widget.y)

    idx = problems_on_page.index(problem)

    problem_above = problems_on_page[idx - 1]

    # Determine y coordinates to search for text
    y_above = problem_above.widget.y + problem_above.widget.height if idx != 0 else 0
    y_current = problem.widget.y + problem.widget.height

    for page in PDFPage.create_pages(document):
        interpreter.process_page(page)
        layout = device.get_result()

        if layout.pageid == problem.widget.page + 1:
            filtered_words = get_words(layout._objs, y_above, y_current, app_config)

            if not filtered_words:
                return ''

            lines = filtered_words[0].split('\n')
            return lines[0]

    return ''


def get_words(layout_objs, y_top, y_bottom, app_config):
    """
    Returns the text from a pdf page within a specified height.

    Parameters
    ----------
    app_config : dict
        Configuration of the app
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
    page_format = app_config.get('PAGE_FORMAT', 'A4')
    page_height = PAGE_FORMATS[page_format][1]

    words = []

    for obj in layout_objs:
        if isinstance(obj, pdfminer3.layout.LTTextBoxHorizontal):
            if page_height - y_top > obj.bbox[1] > page_height - y_bottom:
                words.append(obj.get_text())

        elif isinstance(obj, pdfminer3.layout.LTFigure):
            words.append(get_words(obj._objs, app_config))

    return words
