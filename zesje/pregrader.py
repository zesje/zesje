
from zesje.images import guess_dpi

import zesje.database

# 3 - resolution / dpi to convert points to inches to pixels
# 4 - get corner marker keypoints per page
# 5 - optional? determine blank pdf corner markers vs submission corner markers
# 6 - transform submission image
# 7 - determine checkbox locations
# 8 - get box location and check if it is filled
# 8.5 - check if feedback option exists
# 9 - connect to feedback option

# coupled feedback cannot be deleted

from zesje.database import Exam

from zesje.images import guess_dpi

def pregrade(exam_token, image):
    # get image
    image = None

    exam = Exam.query.get(exam_token=exam_token)

    problems = exam.problems
    mc_options = [problem.mc_options for problem in problems]

    coords = [(cb.x, cb.y) for cb in mc_options]

    pass


def _locate_checkbox():
    pass
