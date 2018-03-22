""" REST api for problems """

from flask_restful import Resource

from pony import orm

from ..models import Exam, Problem

class Problems(Resource):
    """ List of problems associated with a particular exam_id """

    @orm.db_session
    def get(self, exam_id):
        """get list of problems of exam

        Returns
        -------
        list of:
            id: int
            name: str
        """

        exam = Exam[exam_id]

        return [
            {
                'id': problem.id,
                'name': problem.name
            }
            for problem in Problem.select(lambda p: p.exam == exam)
        ]
