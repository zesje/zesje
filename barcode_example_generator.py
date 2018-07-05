from io import BytesIO

from reportlab.pdfgen import canvas
import PIL
from wand.image import Image
from wand.color import Color
from pystrich.datamatrix import DataMatrixEncoder


def generate_datamatrix(exam_id, page_num, copy_num):
    data = f'{exam_id}/{copy_num:04d}/{page_num:02d}'

    image_bytes = DataMatrixEncoder(data).get_imagedata(cellsize=2)
    return PIL.Image.open(BytesIO(image_bytes))


datamatrix = generate_datamatrix(0, 0, 0)
datamatrix_x = datamatrix_y = 0
fontsize = 8
margin = 3

datamatrix = generate_datamatrix(0, 0, 0000)
imagesize = (datamatrix.width, 3 + fontsize + datamatrix.height)

result_pdf = BytesIO()
canv = canvas.Canvas(result_pdf, pagesize=imagesize)

canv.drawInlineImage(datamatrix, 0, 3 + fontsize)

canv.setFont('Helvetica', fontsize)
canv.drawString(0, 3, f"  # 1519")

canv.showPage()
canv.save()

result_pdf.seek(0)

# From https://stackoverflow.com/questions/27826854/python-wand-convert-pdf-to-png-disable-transparent-alpha-channel
with Image(file=result_pdf, resolution=80) as img:
    with Image(width=img.width, height=img.height, background=Color("white")) as bg:
        bg.composite(img, 0, 0)
        bg.save(filename="client/components/barcode_example.png")
