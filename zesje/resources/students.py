from flask_restful import Resource
from pony import orm

from ..models import Student

class Students(Resource):
    """Getting a list of students."""

    @orm.db_session
    def get(self):
        """get all students for the course.

        Returns
        -------
        list of:
            id: int
            first_name: str
            last_name: str
            email: str
        """
        return [
            {
                'id': s.id,
                'firstName': s.first_name,
                'lastName': s.last_name,
                'email': s.email,
            }
            for s in Student.select()
        ]
