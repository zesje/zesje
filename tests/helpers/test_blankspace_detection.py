import pytest
import os
from zesje.helpers import image_helper

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


def test_detect_space_corner(mock_check_space_idwidget_true,
                             mock_check_space_datamatrix_true, datadir):

    blank_pdf = os.path.join(datadir,'blank-a4-2pages.pdf')

    result = image_helper.check_enough_blankspace(blank_pdf)

    for i in range(len(result)):
        assert(result[i])
