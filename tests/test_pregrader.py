import os
import pytest
from PIL import Image
import numpy as np
from zesje import pregrader
from zesje.database import Problem, ProblemWidget
from reportlab.lib.pagesizes import A4


def load_image(datadir, *args):
    path = os.path.join(datadir, *args)
    image = Image.open(path)
    return np.array(image)


@pytest.fixture
def checkbox_images(datadir):
    return {
        dpi: [load_image(datadir, 'checkboxes', f'{image}_{dpi}dpi.jpg')
              for image in ('student', 'reference')]
        for dpi in (100, 300)
    }


@pytest.fixture
def student_aligned(datadir):
    return load_image(datadir, 'blanks', 'student_aligned.jpg')


@pytest.fixture
def student_misaligned(datadir):
    return load_image(datadir, 'blanks', 'student_misaligned.jpg')


@pytest.fixture
def reference(datadir):
    return load_image(datadir, 'blanks', 'reference.jpg')


@pytest.mark.parametrize('dpi', [100, 300],
                         ids=["100 dpi", "300 dpi"])
def test_is_checkbox_filled(dpi, checkbox_images, app):
    student, reference = checkbox_images[dpi]
    amounts = [2, 3, 4, 5]

    unclears = [
        0b00000000000000,
        0b01000000000000,
        0b00000001000000,
        0b00000000000000,
        0b00000000000000,
        0b00000001000000,
    ]

    expecteds = [
        0b01100101001010,
        0b10010110011010,
        0b10101110010100,
        0b11010101001011,
        0b11100100101010,
        0b10110101011100,
    ]

    spacing_y = 75
    spacing_x = 110

    xs = 50 + np.arange(len(amounts)) * spacing_x
    ys = int(A4[1]) - (int(A4[1]) - 300 - np.arange(6) * spacing_y)
    n = sum(amounts)

    for y, expected, unclear in zip(ys, expecteds, unclears):
        index = n - 1
        for x, amount in zip(xs, amounts):
            for i in range(amount):
                # We should not be too strict, different algorithms can produce slightly
                # different results, which causes the threshold to be just (not) reached.
                if unclear & 1 << index:
                    continue

                xi = x + 20 * (i + 1)
                yi = y + 20

                expected_result = bool(expected & 1 << index)
                assert pregrader.is_checkbox_filled((xi, yi), student, reference) == expected_result

                index -= 1


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


def test_threshold(config_app, datadir):
    dir = os.path.join(datadir, 'thresholds')
    files = os.listdir(dir)
    for filename in files:
        img = Image.open(os.path.join(dir, filename))
        problem = Problem(name='Problem')
        problem.widget = ProblemWidget(x=0, y=0, width=img.size[0], height=img.size[1])

        data = np.array(img)
        reference = np.full_like(data, 255)

        assert not pregrader.is_blank(problem, data, reference)
