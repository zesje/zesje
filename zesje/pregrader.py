# 3 - resolution / dpi to convert points to inches to pixels
# 4 - get corner marker keypoints per page
# 5 - optional? determine blank pdf corner markers vs submission corner markers
# 6 - transform submission image
# 7 - determine checkbox locations
# 8 - get box location and check if it is filled
# 8.5 - check if feedback option exists
# 9 - connect to feedback option

# coupled feedback cannot be deleted

from zesje.database import db, Exam, Submission, Solution, Problem


def pregrade(exam_token, image):
    # get image
    image = None

    exam = Exam.query.get(exam_token=exam_token)

    problems = exam.problems

    mc_options = [problem.mc_options for problem in problems]

    coords = [(cb.x, cb.y) for cb in mc_options]

    pass


def add_feedback_to_solution(submission, page, page_img, corner_keypoints):
    """
    Adds the multiple choice options that are identified as marked as a feedback option to a solution

    Params
    ------
    page_img: image of the page
    barcode: data from the barcode on the page
    """
    problems_on_page = Problem.query.filter(Problem.widget.page == page).all()

    for problem in problems_on_page:
        for mc_option in problem.mc_options:
            box = (mc_option.x, mc_option.y)

            sol = Solution.query.filter(Solution.problem_id == problem.id).one_or_none()

            # check if box is filled
            if box_is_filled(box, page_img, corner_keypoints):
                sol.feedback.append(mc_option.feedback)
                db.session.commit()


def box_is_filled(box, page_img, corner_keypoints):
    pass


def _locate_checkbox():
    pass
