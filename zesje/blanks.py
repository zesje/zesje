import cv2
import numpy as np

from .database import db, Exam, Problem
from .images import guess_dpi, get_box
from .scans import extract_images




def set_blank(pdf_path, exam_id):
    pages = extract_images(pdf_path)
    exam = Exam.query.filter(Exam.token == exam_id).first()
    page_num = 0

    for image, page in pages :

        problems_on_page = [problem for problem in exam.problems if problem.widget.page == page_num]
        page_num = page_num + 1
        for problem in problems_on_page:
            widget_area = np.asarray([
                problem.widget.y,  # top
                problem.widget.y + problem.widget.height,  # bottom
                problem.widget.x,  # left
                problem.widget.x + problem.widget.width,  # right
            ])
            page_img = np.array(image)
            widget_area_in = widget_area / 72

            cut_im = get_box(page_img, widget_area_in, padding=0)
            gray = cv2.cvtColor(cut_im, cv2.COLOR_BGR2GRAY)

            ret,thresh = cv2.threshold(gray,180,255,3)
            kernel = np.ones((3,3),np.uint8)
            timp = cv2.dilate(~thresh,kernel,iterations = 2)
            ret, temp = cv2.threshold(timp,180,255,3)
            contours,h = cv2.findContours(~temp,1,2)
            a = 80
            value = 0
            for cnt in contours:   
                if cv2.contourArea(cnt) > a:
                    value = value+1

            problem.blank_threshold = value
            db.session.commit()
