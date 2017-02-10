import os
import random
from datetime import datetime

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


# feedback option for a single problem
class FeedbackOption(db.Entity):
    problems = Set(Problem)
    text = Required(str, unique=True)
    solutions = Set('Solution')


# solution to a single problem
class Solution(db.Entity):
    submission = Required(Submission)
    graded_by = Optional(Grader)  # if null, this has not yet been graded
    graded_at = Optional(datetime)
    problem = Required(Problem)
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

    names = """\
        Reggie Miron
        Allyn Whitis
        Davida Buda
        Kristie Stubblefield
        Zoraida Loudon
        Madge Rogge
        Marylyn Folkes
        Sindy Judy
        Therese Jourdan
        Kassie Pinion
        Angella Rudloff
        Trudie Freas
        Tayna Mule
        Tami Hippert
        Blanche Alvidrez
        Rupert Wolken
        Madalyn Watkins
        Reita Lubinsky
        Johnny Paules
        Lenita Weddell
        Lieselotte Scarpa
        Eda Koelling
        Cary Gallaher
        Ebonie Brathwaite
        Shane Pugsley
        Velva Cranston
        Stefan Joesph
    """.split('\n')[:-1]  # remove last newline

    grader_names = [name.strip().split() for name in grader_names]
    student_names = [name.strip().split() for name in names]
    # numbers with 7 digits
    student_ids = [random.randint(10**6, 10**7 - 1) for name in names]
    feedback_options = ['Everything correct', 'No solution provided']


    with db_session:
        # problems and default feedback options
        for name in ['1', '2a', '2b', '2c', '2d']:
            Problem(name=name)
        problems = Problem.select() ;
        for fb in feedback_options:
            FeedbackOption(text=fb, problems=problems)


        # students and submissions
        for (first_name, last_name), student_id in zip(student_names, student_ids):
            Student(first_name=first_name, last_name=last_name, id=student_id)
            sub = Submission()
            for p in problems:
                Solution(problem=p, image_path='/', submission=sub)

        # graders
        for first_name, last_name in grader_names:
            Grader(first_name=first_name, last_name=last_name)


    with db_session:
        Grader.select().show()
        Student.select().show()


if __name__ == '__main__':
    main()
else:
    db.generate_mapping(create_tables=True)
