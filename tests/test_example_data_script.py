import os


def test_example_data_script():
    result_code = os.system('python3 example_data.py --exams 1 --students 1 --graders 2')
    assert result_code == 0
