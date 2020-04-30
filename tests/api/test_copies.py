import pytest

from itertools import product

from zesje.database import db, Submission, Exam, Student, Copy

copy_count = 0


@pytest.fixture
def app_with_data(app):
    with app.app_context():
        exam = Exam(name='')
        students = [Student(id=i, first_name='', last_name='') for i in range(5)]
        db.session.add(exam)
        for student in students:
            db.session.add(student)
        db.session.commit()
        yield app, exam, students


types = ['unvalidated',
         'unvalidated_multiple',
         'validated',
         'validated_multiple',
         'mixed',
         'mixed_multiple']


def next_copy():
    global copy_count
    copy_count += 1
    return Copy(number=copy_count)


def add_submissions(exam, student, type, with_student=True):
    subs = []
    student_none = student if with_student else None
    if type == 'unvalidated':
        subs.append(Submission(exam=exam, student=student_none, copies=[next_copy()]))
    elif type == 'unvalidated_multiple':
        subs.append(Submission(exam=exam, student=student_none, copies=[next_copy()]))
        subs.append(Submission(exam=exam, student=student, copies=[next_copy()]))
    elif type == 'validated':
        subs.append(Submission(exam=exam, student=student, validated=True, copies=[next_copy()]))
    elif type == 'validated_multiple':
        subs.append(Submission(exam=exam, student=student, validated=True, copies=[next_copy(), next_copy()]))
    elif type == 'mixed':
        subs.append(Submission(exam=exam, student=student_none, copies=[next_copy()]))
        subs.append(Submission(exam=exam, student=student, validated=True, copies=[next_copy()]))
    elif type == 'mixed_multiple':
        subs.append(Submission(exam=exam, student=student_none, copies=[next_copy()]))
        subs.append(Submission(exam=exam, student=student, copies=[next_copy()]))
        subs.append(Submission(exam=exam, student=student, validated=True, copies=[next_copy(), next_copy()]))

    for sub in subs:
        db.session.add(sub)
    db.session.commit()
    return [(sub, [copy for copy in sub.copies]) for sub in subs]


def assert_valid_state():
    for sub in Submission.query.all():
        if sub.validated:
            assert len(sub.copies) >= 1
            assert sub.student is not None
        else:
            assert len(sub.copies) <= 1


def assert_exactly(sub, copies, student, validated=True):
    assert sub in db.session
    assert sub.student == student
    assert sub.validated is validated
    assert len(sub.copies) == len(copies)
    for copy in copies:
        assert copy in sub.copies


def validate(copy, student, exam, test_client, returns_ok=True):
    response = test_client.put(f'/api/copies/{exam.id}/{copy.number}', data={'studentID': student.id})
    if returns_ok:
        assert response.status_code == 200

    assert_valid_state()


@pytest.mark.parametrize('with_student', [True, False], ids=['same_student', 'no_student'])
def test_unvalidated(test_client, app_with_data, with_student):
    app, exam, students = app_with_data
    student = students[0]
    sub, copies = add_submissions(exam, student, 'unvalidated', with_student)[0]
    validate(copies[0], student, exam, test_client)

    assert_exactly(sub, copies, student)


def test_validated(test_client, app_with_data):
    app, exam, students = app_with_data
    student = students[0]
    sub, copies = add_submissions(exam, student, 'validated')[0]
    validate(copies[0], student, exam, test_client)

    assert_exactly(sub, copies, student)


@pytest.mark.parametrize('with_student', [True, False], ids=['same_student', 'no_student'])
def test_unvalidated_multiple(test_client, app_with_data, with_student):
    app, exam, students = app_with_data
    student = students[0]
    unvalidated1, unvalidated2 = add_submissions(exam, student, 'unvalidated_multiple', with_student)
    sub, copies = unvalidated1
    validate(copies[0], student, exam, test_client)

    assert_exactly(sub, copies, student)
    assert_exactly(*unvalidated2, student, validated=False)


def test_validated_multiple(test_client, app_with_data):
    app, exam, students = app_with_data
    student = students[0]
    sub_copies = add_submissions(exam, student, 'validated_multiple')
    sub, copies = sub_copies[0]

    validate(copies[0], student, exam, test_client)

    assert_exactly(sub, copies, student)


@pytest.mark.parametrize('with_student', [True, False], ids=['same_student', 'no_student'])
def test_mixed_unvalidated(test_client, app_with_data, with_student):
    app, exam, students = app_with_data
    student = students[0]
    to_validate, validated = add_submissions(exam, student, 'mixed', with_student)
    sub, copies = to_validate
    sub2, copies2 = validated

    validate(copies[0], student, exam, test_client)

    if sub2 in db.session:
        sub, sub2 = sub2, sub

    assert_exactly(sub, copies + copies2, student)
    assert sub2 not in db.session


def test_mixed_validated(test_client, app_with_data):
    app, exam, students = app_with_data
    student = students[0]
    unvalidated, to_validate = add_submissions(exam, student, 'mixed')
    sub, copies = to_validate
    sub2, copies2 = unvalidated

    validate(copies[0], student, exam, test_client)

    assert_exactly(sub, copies, student)
    assert_exactly(sub2, copies2, student, validated=False)


@pytest.mark.parametrize('with_student', [True, False], ids=['same_student', 'no_student'])
def test_mixed_multiple_unvalidated(test_client, app_with_data, with_student):
    app, exam, students = app_with_data
    student = students[0]
    unvalidated1, unvalidated2, validated = add_submissions(exam, student, 'mixed_multiple', with_student)
    sub, copies = unvalidated1
    subv, copiesv = validated

    validate(copies[0], student, exam, test_client)

    if sub in db.session:
        sub, subv = subv, sub

    assert_exactly(subv, copies + copiesv, student)
    assert sub not in db.session
    assert_exactly(*unvalidated2, student, validated=False)


def test_mixed_multiple_validated(test_client, app_with_data):
    app, exam, students = app_with_data
    student = students[0]
    unvalidated1, unvalidated2, validated = add_submissions(exam, student, 'mixed_multiple')
    sub, copies = validated

    validate(copies[0], student, exam, test_client)

    assert_exactly(sub, copies, student)
    assert_exactly(*unvalidated1, student, validated=False)
    assert_exactly(*unvalidated2, student, validated=False)


old_student_types = ['unvalidated', 'validated']
new_student_types = ['validated', 'validated_multiple']
student_types = list(product(old_student_types, new_student_types))


@pytest.mark.parametrize(['old_student_type', 'new_student_type'], student_types,
                         ids=['_'.join(student_type) for student_type in student_types])
def test_switch_single(test_client, app_with_data, old_student_type, new_student_type):
    app, exam, students = app_with_data
    student_old = students[0]
    sub_old, copies_old = add_submissions(exam, student_old, old_student_type)[0]

    student_new = students[1]
    sub_new, copies_new = add_submissions(exam, student_old, new_student_type)[0]

    validate(copies_old[0], student_new, exam, test_client)

    if sub_old in db.session:
        sub_old, sub_new = sub_new, sub_old

    assert_exactly(sub_new, copies_old + copies_new, student_new)
    assert sub_old not in db.session
