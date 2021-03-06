import pytest


@pytest.mark.parametrize('email', ['student@school.edu', ''], ids=['email', 'no email'])
def test_add_student(test_client, email):
    student = new_student(1000000, email)
    result = test_client.put('api/students', json=student)

    assert result.status_code == 200

    data = result.get_json()
    assert data == student


def test_get_students(test_client):
    students = [
        new_student(1000000, ''),
        new_student(1000001, 'student@school.edu')
    ]

    for student in students:
        assert test_client.put('api/students', json=student).status_code == 200

    result = test_client.get('api/students')
    assert result.status_code == 200

    data = result.get_json()
    assert len(data) == len(students)

    # Rename 'id' key to 'studentID' to match the request JSON
    for student_data in data:
        student_data['studentID'] = student_data.pop('id')

    for student in students:
        assert student in data


# Data is in the format [id, first, last, email]
@pytest.mark.parametrize('data,code,expected', [
    ([[1000000, 'a', 'b', 'c'], [1000000, 'a2', 'b2', 'c']], [200, 200], [[1000000, 'a2', 'b2', 'c']]),
    ([[1000000, 'a', 'b', 'c'], [1000001, 'a2', 'b2', 'c']], [200, 400], [[1000000, 'a', 'b', 'c']]),
    ([[1000000, 'a', 'b', 'c'], [1000000, 'a2', 'b2', 'c2']], [200, 200], [[1000000, 'a2', 'b2', 'c2']]),
    ([[1000000, 'a', 'b', 'c'], [1000000, 'a2', 'b2', '']], [200, 200], [[1000000, 'a2', 'b2', None]]),
    ([[1000000, 'a', 'b', 'c'], [1000001, 'a2', 'b2', 'c2'], [1000001, 'a3', 'b3', 'c']], [200, 200, 400],
     [[1000000, 'a', 'b', 'c'], [1000001, 'a2', 'b2', 'c2']]),
], ids=['same id same email', 'new id same email', 'same id new mail', 'same id no mail', 'update id same mail'])
def test_update_students(test_client, data, code, expected):
    for index, student_data in enumerate(data):
        student = new_student(student_data[0], student_data[3], student_data[1], student_data[2])
        assert test_client.put('api/students', json=student).status_code == code[index]

    result = test_client.get('api/students')
    assert result.status_code == 200

    data = result.get_json()
    assert len(data) == len(expected)

    data = list(map(lambda d: list(d.values()), data))

    for student in expected:
        assert student in data


def new_student(id, mail, first='First', last='Last'):
    return {
        'studentID': id,
        'firstName': first,
        'lastName': last,
        'email': mail or None
    }
