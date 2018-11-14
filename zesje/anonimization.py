import functools
import itertools
import math
import os
import platform
from collections import namedtuple, Counter
from io import BytesIO
import signal

from pony import orm
import numpy as np
from PIL import Image
from PIL import ImageEnhance
from PIL import ImageFilter
import PyPDF2
image = Image.open("1.jpeg")

straight_line = np.array(([1,5,1],
                        [1,5,1],
                        [1,5,1]), dtype="int")

#function to filter out color values above a certain threshold
def remove_colorvalues(img, threshold):
    #img = img.filter(ImageFilter.BLUR)
    sharpener = ImageEnhance.Sharpness(img)
    sharpener.enhance(2)
    px = img.load()
    width, height = img.size
    print(width,height)
    for x in range(0, width):
        for y in range(0,height):
            if(sum(px[x,y])>threshold or max(px[x,y])>80):
                px[x,y]=(255,255,255)

#function to filter out unstraight lines
def conv(img, kernel):
    return np.convolve(img,kernel)



#Function to extract images out of a pdf (similar to extract_images from the zesje project)
def extract_images(filename):
    """Yield all images from a PDF file.

    Adapted from https://stackoverflow.com/a/34116472/2217463

    We raise if there are > 1 images / page
    """
    reader = PyPDF2.PdfFileReader(open(filename, "rb"))
    total = reader.getNumPages()
    for pagenr in range(total):
        page = reader.getPage(pagenr)
        xObject = page['/Resources']['/XObject'].getObject()

        if sum((xObject[obj]['/Subtype'] == '/Image')
               for obj in xObject) > 1:
            raise RuntimeError("error")#f'Page {pagenr + 1} contains more than 1 image,'
                               #'likely not a scan')

        for obj in xObject:
            if xObject[obj]['/Subtype'] == '/Image':
                data = xObject[obj].getData()
                filter = xObject[obj]['/Filter']

                if filter == '/FlateDecode':
                    size = (xObject[obj]['/Width'], xObject[obj]['/Height'])
                    if xObject[obj]['/ColorSpace'] == '/DeviceRGB':
                        mode = "RGB"
                    else:
                        mode = "P"
                    img = Image.frombytes(mode, size, data)
                else:
                    img = Image.open(BytesIO(data))

                if img.mode == 'L':
                    img = img.convert('RGB')

                yield img, pagenr+1

#Make an array of images, remove for each image the color values outside the threshold
#then save it in a new pdf
images=[]
for image, page in extract_images("testpdf.pdf"):
    #image.show()
    remove_colorvalues(image, 200)
    rotation = 180+(90-(page%2*180))
    images = images +[image.rotate(rotation, expand=True)]
    print("page "+str(page)+" is done." )
#image.show()
images[0].save("out.pdf", save_all=True, append_images=images[1:])



#print(total)
#enhancer = ImageEnhance.Color(image)
#enhancer2 = ImageEnhance.Contrast(enhancer.enhance(0))
#enhancer2.enhance(1).show()
