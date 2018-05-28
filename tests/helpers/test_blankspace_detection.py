import pytest
import os
from zesje.helpers import image_helper


# Mocks
# Used to isolate the condition in check_enough_blankspace for testing purposes
@pytest.fixture
def mock_check_space_datamatrix_true(monkeypatch):
    def mock_return(bin_im):
        return True
    monkeypatch.setattr(image_helper, 'check_space_datamatrix',
                        mock_return)


@pytest.fixture
def mock_check_space_idwidget_true(monkeypatch):
    def mock_return(bin_im):
        return True
    monkeypatch.setattr(image_helper, 'check_space_idwidget',
                        mock_return)


@pytest.fixture
def mock_check_space_corner_true(monkeypatch):
    def mock_return(bin_im):
        return True
    monkeypatch.setattr(image_helper, 'check_space_corner',
                        mock_return)


# Tests

@pytest.mark.parametrize('name',
                         os.listdir(os.path.join('tests',
                                                 'data',
                                                 'source_exams',
                                                 'compatible')),
                         ids=os.listdir(os.path.join('tests',
                                                     'data',
                                                     'source_exams',
                                                     'compatible')))
def test_detect_space_corner_compatible(name, datadir,
                                        mock_check_space_datamatrix_true,
                                        mock_check_space_idwidget_true):

    pdf_path = os.path.join(datadir, 'source_exams', 'compatible', f'{name}')
    result = image_helper.check_enough_blankspace(pdf_path)

    for i in range(len(result)):
        assert(result[i])


@pytest.mark.parametrize('name',
                         os.listdir(os.path.join('tests',
                                                 'data',
                                                 'source_exams',
                                                 'incompatible')),
                         ids=os.listdir(os.path.join('tests',
                                                     'data',
                                                     'source_exams',
                                                     'incompatible')))
def test_detect_space_corner_incompatible(name, datadir,
                                          mock_check_space_datamatrix_true,
                                          mock_check_space_idwidget_true):

    pdf_path = os.path.join(datadir, 'source_exams', 'incompatible', f'{name}')
    result = image_helper.check_enough_blankspace(pdf_path)

    for i in range(len(result)):
        assert not(result[i])


def test_detect_space_datamatrix_incompatible(datadir,
                                              mock_check_space_corner_true,
                                              mock_check_space_idwidget_true):

    pdf_path = os.path.join(datadir, 'black-a4-2pages.pdf')
    result = image_helper.check_enough_blankspace(pdf_path)

    for i in range(len(result)):
        assert not(result[i])


def test_detect_space_datamatrix_compatible(datadir,
                                            mock_check_space_corner_true,
                                            mock_check_space_idwidget_true):

    pdf_path = os.path.join(datadir, 'blank-a4-2pages.pdf')
    result = image_helper.check_enough_blankspace(pdf_path)

    for i in range(len(result)):
        assert(result[i])
