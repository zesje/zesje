
import sys
import os
from io import BytesIO

from reportlab.pdfgen import canvas
from wand.image import Image
from wand.color import Color

sys.path.append(os.getcwd())

from zesje.pdf_generation import generate_datamatrix  # noqa: E402
from zesje.database import token_length  # noqa: E402


exam_token = "A" * token_length
copy_num = 159
page_num = 0

fontsize = 12
datamatrix_x = 0
datamatrix_y = fontsize

datamatrix = generate_datamatrix(exam_token, page_num, copy_num)
imagesize = (datamatrix.width, fontsize + datamatrix.height)

result_pdf = BytesIO()
canv = canvas.Canvas(result_pdf, pagesize=imagesize)

canv.drawInlineImage(datamatrix, datamatrix_x, datamatrix_y)

canv.setFont('Helvetica', fontsize)
canv.drawString(datamatrix_x, datamatrix_y - (fontsize * 0.66),
                f" # {copy_num}")

canv.showPage()
canv.save()

result_pdf.seek(0)

# From https://stackoverflow.com/questions/27826854/python-wand-convert-pdf-to-png-disable-transparent-alpha-channel
with Image(file=result_pdf, resolution=72) as img:
    with Image(width=imagesize[0], height=imagesize[1], background=Color("white")) as bg:
        bg.composite(img, 0, 0)
        bg.save(filename="client/components/barcode_example.png")
