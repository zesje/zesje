from flask_restful import Resource
from pony import orm

from ..models import Student

class Students(Resource):
    """Getting a list of students."""

    @orm.db_session
    def get(self, student_id=None):
        """get all students for the course.

         Parameters
        ----------
        student_id : int, optional
            The ID of the student, often the studentnumber but mainly used as unique identifier

        Returns
        -------
        If a valid 'student_id' is provided the single instance of the student will be returned:
            id: int
            first_name: str
            last_name: str
            email: str 

        If no student_id is provided the entire list of students will be returned.
        """

        if student_id is not None:
            s = Student.get(id=student_id)
            if not s:
                raise orm.core.ObjectNotFound(Student)
            return {
                'id': s.id,
                'firstName': s.first_name,
                'lastName': s.last_name,
                'email': s.email,
            }


        return [
            {
                'id': s.id,
                'firstName': s.first_name,
                'lastName': s.last_name,
                'email': s.email,
            }
            for s in Student.select()
        ]
