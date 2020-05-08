import pytest


from zesje.raw_scans import extract_image_info


@pytest.mark.parametrize('file_name, info', [
    ('1234567-02.png', (1234567, 1, 1)),
    ('1234567-1-4.jpeg', (1234567, 0, 4)),
    ('1234567.png', None),
    ('ABCDEFG.jpeg', None)],
    ids=[
    'Valid name (no copy)',
    'Valid name (with copy)',
    'Invalid name (no page)',
    'Invalid name (no student)'])
def test_extract_image_info(file_name, info):
    try:
        ext_info = extract_image_info(file_name)
    except Exception:
        ext_info = None

    assert ext_info == info
