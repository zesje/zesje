import os

import pytest
import numpy as np
from PIL import Image
from reportlab.pdfgen import canvas
from pdfrw import PdfReader, PdfWriter, PageMerge
from tempfile import NamedTemporaryFile

from zesje.scans import decode_barcode, ExamMetadata, ExtractedBarcode
from zesje import scans


# Returns the original image instead of retrieving a box from it
@pytest.fixture
def mock_get_box_return_original(monkeypatch, datadir):
    def mock_return(image, widget, padding):
        return image
    monkeypatch.setattr(scans, 'get_box', mock_return)


# Tests whether the output of calc angle is correct
@pytest.mark.parametrize('image_filename, token, expected', [
    ('COOLTOKEN_0005_01.png', 'COOLTOKEN', ExtractedBarcode('COOLTOKEN',   5,   1)),
    ('COOLTOKEN_0050_10.png', 'COOLTOKEN', ExtractedBarcode('COOLTOKEN',   50, 10)),
    ('TOKENCOOL_9999_99.png', 'TOKENCOOL', ExtractedBarcode('TOKENCOOL', 9999, 99))],
    ids=['Simple test 1', 'Simple test 2', 'High numbers'])
def test_decode_barcode(datadir, image_filename, token, expected, mock_get_box_return_original):

    image_path = os.path.join(datadir, 'datamatrices', image_filename)

    exam_config = ExamMetadata(
        token=token,
        barcode_area=[0],
        student_id_widget_area=None,
        problem_ids=None
    )

    image = np.array(Image.open(image_path))

    assert decode_barcode(image, exam_config) == (expected, False)


def generate_page(width = 827, height = 1169):
    """
    Generate blank page with the specified width and height
    """
    pdf = np.zeros((height, width))
    pdf.fill(255)
    return Image.fromarray(pdf).convert("RGB")

def generate_multiple_pages(pages=5):
    """
    generate multiple white pages
    """
    images=[]
    for i in range(0, pages):
        images = images + [generate_page()]
    return images

def apply_whitenoise(data, threshold =0.98):
    """
    Apply white noise to the image
    """
    shape = data.shape
    for i in range(0,shape[0]):
        for j in range(0,shape[1]):
            data[i,j]= data[i,j][0] * (randint(threshold*1000,1000)/1000)
            data[i,j]= data[i,j][1] * (randint(threshold*1000,1000)/1000)
            data[i,j]= data[i,j][2] * (randint(threshold*1000,1000)/1000)
    return data

def apply_tranformation(pdf):
    """
    General structure for applying a transformation to the picture
    """
    images = []
    for image, page in scans.extract_images(pdf):
        image.load()
        data = np.asarray(image.convert("RGB"))
        data = apply_whitenoise(data,0.9)
        #rotation = 180+(90-(page%2*180))
        images = images +[Image.fromarray(data).convert("RGB")]
        #images = images +[image]
        print("page "+str(page)+" is done." )
    #image.show()
    images[0].save("noise.pdf", save_all=True, append_images=images[1:])



def test_pipeline():
    """
    Generate exam Metadata
    Make PDF according to the Metadata
    Apply fuzzying Transformations
    Read PDF using Metadata
    clean up any leftover files
    """
    #exam_id = 1
    exam_config = ExamMetadata(
        token="id",
        barcode_area=[0,100,0,100],
        student_id_widget_area=None,
        problem_ids=None
    )
    datamatrix_x = exam_config.barcode_area[2]
    datamatrix_y = exam_config.barcode_area[0]
    pdf = generate_multiple_pages(5)
    pdf[0].save("outTest.pdf", save_all=True, append_images=pdf[1:])
    pdf_generation.generate_pdfs("outTest.pdf", "id", [145], ["/home/lenty/Documents/zesje/debug/1.pdf"], 200, 200, datamatrix_x, datamatrix_y)
    #pdf_name = mock_pdf_generation(exam_config)

    for image, page in scans.extract_images("/home/lenty/Documents/zesje/debug/1.pdf"):
        success, reason = scans.process_page(image, exam_config, "/home/lenty/Documents/zesje/debug")
        #print(reason)
        #assert success == True
    os.remove("outTest.pdf")
    os.remove("/home/lenty/Documents/zesje/debug/1.pdf")








def mock_pdf_generation(exam_config):
    """
    Generate Blank Pdf
    Add Cornermarks to the Pdf
    Pass pdf to extract cornermarks
    """
    fontsize = 8
    image = generate_multiple_pages(1)
    image[0].save("outTest.pdf", save_all=True, append_images=image[1:])
    size = image[0].size
    print(size)

    exam_id = exam_config.token
    datamatrix_x = exam_config.barcode_area[2]+10
    datamatrix_y = exam_config.barcode_area[0]+10 #Unsure what the exact coordinates are


    with NamedTemporaryFile() as cornermarks:
        overlay = canvas.Canvas(cornermarks.name, pagesize=size)
        pdf_generation._add_corner_markers_and_bottom_bar(overlay, size)
        datamatrix = pdf_generation.generate_datamatrix(exam_id, 1, 1)
        # transform y-cooridate to different origin location
        datamatrix_y_adjusted = size[1] - datamatrix_y - datamatrix.height
        overlay.drawInlineImage(datamatrix, datamatrix_x, datamatrix_y_adjusted)
        overlay.drawString(
            datamatrix_x, datamatrix_y_adjusted - fontsize,
            f" # {1}"
        )


        overlay.save()

        exam_pdf = PdfReader("outTest.pdf")
        overlay_pdf = PdfReader(cornermarks)
        for page_idx, exam_page in enumerate(exam_pdf.pages):
            overlay_merge = PageMerge().add(overlay_pdf.pages[0])[0]
            exam_merge = PageMerge(exam_page).add(overlay_merge)
            exam_merge.render()
        PdfWriter("output_canvas.pdf", trailer=exam_pdf).write()


    os.remove("outTest.pdf")
    return "output_canvas.pdf"
    #overlay_canv = canvas.Canvas(overlay_file.name, pagesize=pagesize)
    #make and  Pdf
    #Apply cornermarks
    #save PDF
    #Check cornermarks
    #delete PDF

test_pipeline()
test_blank_pipeline()



# Untested:
# - def process_pdf()
# - def extract_images()
# - def write_pdf_status()
# - def process_page()
# - def guess_dpi()
# - def rotate_image()
# - def shift_image()
# - get_student_number()
#   Not tested in this file. See: test_get_studentnumber_precision.py
