import os
import pytest
from PIL import Image
import numpy as np
from zesje import pregrader
from zesje.database import Problem, ProblemWidget


def load_image(datadir, *args):
    path = os.path.join(datadir, *args)
    image = Image.open(path)
    return np.array(image)


@pytest.fixture
def scanned_page(datadir):
    return load_image(datadir, 'checkboxes', 'scanned_page.jpg')


@pytest.fixture
def student_aligned(datadir):
    return load_image(datadir, 'blanks', 'student_aligned.jpg')


@pytest.fixture
def student_misaligned(datadir):
    return load_image(datadir, 'blanks', 'student_misaligned.jpg')


@pytest.fixture
def reference(datadir):
    return load_image(datadir, 'blanks', 'reference.jpg')


@pytest.mark.parametrize('box_coords, result', [((346, 479), True), ((370, 479), False), ((393, 479), True),
                                                ((416, 479), True), ((439, 479), True), ((155, 562), True)],
                         ids=["1 filled", "2 empty", "3 marked with line", "4 completely filled",
                              "5 marked with an x", "e marked with a cirle inside"])
def test_ideal_crops(box_coords, result, scanned_page):
    assert pregrader.box_is_filled(box_coords, scanned_page, cut_padding=0.1, box_size=9) == result


@pytest.mark.parametrize('box_coords, result', [((341, 471), True), ((352, 482), True), ((448, 482), True),
                                                ((423, 474), True), ((460, 475), False), ((477, 474), True),
                                                ((87, 556), False)],
                         ids=["1 filled bottom right", "1 filled top left", "5 filled with a bit of 6",
                              "4 fully filled with the label", "6 empty with label",
                              "7 partially  cropped, filled and a part of 6", "B empty with cb at the bottom"])
def test_shifted_crops(box_coords, result, scanned_page):
    assert pregrader.box_is_filled(box_coords, scanned_page, cut_padding=0.1, box_size=9) == result


@pytest.mark.parametrize('box_coords, result', [((60, 562), True), ((107, 562), True),
                                                ((131, 562), False)],
                         ids=["A filled with trailing letter", "C filled with letters close",
                              "D blank with trailing letter"])
def test_trailing_text(box_coords, result, scanned_page):
    assert pregrader.box_is_filled(box_coords, scanned_page, cut_padding=0.1, box_size=9) == result


problems_with_result = [
    ((60, 154, 483, 206), True),
    ((34, 135, 535, 247), True),
    ((58, 459, 483, 121), False),
    ((46, 448, 504, 141), False),
    ((59, 616, 482, 119), False),
    ((27, 585, 544, 184), False)]


@pytest.mark.parametrize(
    'coords, result', problems_with_result,
    ids=['blank', 'blank padding', 'not blank 1', 'not blank 1 padding', 'not blank 2', 'not blank 2 padding'])
def test_is_blank(config_app, coords, result, student_aligned, reference):
    problem = Problem(name='Problem')
    problem.widget = ProblemWidget(x=coords[0], y=coords[1],
                                   width=coords[2], height=coords[3])

    assert not pregrader.is_problem_misaligned(problem, student_aligned, reference)
    assert pregrader.is_blank(problem, student_aligned, reference) == result


@pytest.mark.parametrize(
    'coords', map(lambda tup: tup[0], problems_with_result),
    ids=['blank', 'blank padding', 'not blank 1', 'not blank 1 padding', 'not blank 2', 'not blank 2 padding'])
def test_is_misaligned(config_app, coords, student_misaligned, reference):
    problem = Problem(name='Problem')
    problem.widget = ProblemWidget(x=coords[0], y=coords[1],
                                   width=coords[2], height=coords[2])

    assert pregrader.is_problem_misaligned(problem, student_misaligned, reference)
