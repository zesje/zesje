import os
from datetime import datetime
import pandas  # Maybe an overkill for a simple read_csv

from pony.orm import Database, Required, Optional, PrimaryKey, Set, db_session


db = Database()

if __name__ != '__main__':
    db.bind('sqlite', os.getcwd() + '/database.sqlite')


# this will be initialized @ app initialization and immutable from then on
class Student(db.Entity):
    id = PrimaryKey(int)
    first_name = Required(str)
    last_name = Required(str)
    email = Optional(str, unique=True)
    submission = Optional('Submission')


# this will be initialized @ app initialization and immutable from then on
class Submission(db.Entity):
    solutions = Set('Solution')
    student = Optional(Student)


# this will be initialized @ app initialization and immutable from then on
class Grader(db.Entity):
    first_name = Required(str)
    last_name = Required(str)
    graded_solutions = Set('Solution')


# this will be initialized @ app initialization and immutable from then on
class Problem(db.Entity):
    name = Required(str)
    feedback_options = Set('FeedbackOption')
    solutions = Set('Solution')


# feedback option -- can be shared by multiple problems.
# this means non-duplicate rows for things like 'all correct',
# but means that care must be taken when "updating" and "deleting"
# options from the UI (not yet supported)
class FeedbackOption(db.Entity):
    problems = Set(Problem)
    text = Required(str, unique=True)
    solutions = Set('Solution')


# solution to a single problem
class Solution(db.Entity):
    submission = Required(Submission)
    problem = Required(Problem)
    PrimaryKey(submission, problem)  # enforce uniqueness on this pair

    graded_by = Optional(Grader)  # if null, this has not yet been graded
    graded_at = Optional(datetime)
    image_path = Required(str)
    feedback = Set(FeedbackOption)
    remarks = Optional(str)


def main():
    db_file = os.getcwd() + '/database.sqlite'
    try:
        os.remove(db_file)
    except OSError:
        pass
    db.bind('sqlite', db_file, create_db=True)
    db.generate_mapping(create_tables=True)

    grader_names = """\
        Wanetta Sporer
        Anthony Olden
        Saran Larusso
    """.split('\n')[:-1]

    grader_names = [name.strip().split() for name in grader_names]
    feedback_options = ['Everything correct', 'No solution provided']

    with db_session:
        # problems and default feedback options
        for name in ['1', '2a', '2b', '2c', '2d']:
            Problem(name=name)
        problems = Problem.select() ;
        for fb in feedback_options:
            FeedbackOption(text=fb, problems=problems)

        # students and submissions
        students = pandas.read_csv('students.csv', skipinitialspace=True,
                                   header=None)
        for student_id, first_name, last_name, email in students.values:
            Student(first_name=first_name, last_name=last_name, id=student_id,
                    email=(email if not pandas.isnull(email) else None))
            sub = Submission()
            for prob in problems:
                Solution(problem=prob,
                         image_path='submissions/{}/{}.png'.format(sub.id, prob.id),
                         submission=sub)

        # graders
        for first_name, last_name in grader_names:
            Grader(first_name=first_name, last_name=last_name)


    with db_session:
        print('Graders\n' + '-' * 7)
        Grader.select().show()
        print()
        print('Students\n' + '-' * 8)
        Student.select().show()


if __name__ == '__main__':
    main()
else:
    db.generate_mapping(create_tables=True)
