
from zesje.images import guess_dpi

import zesje.database

# 1 - get image
# 2 - get database coordinates of all mc_options in exam
# 3 - resolution / dpi to convert points to inches to pixels
# 4 - get corner marker keypoints per page
# 5 - optional? determine blank pdf corner markers vs submission corner markers
# 6 - transform submission image
# 7 - determine checkbox locations
# 8 - get box location and check if it is filled
# 8.5 - check if feedback option exists
# 9 - connect to feedback option

# coupled feedback cannot be deleted


def pregrade(exam_id):
    # Get exam pages

    pass


def _locate_checkbox():
    pass
