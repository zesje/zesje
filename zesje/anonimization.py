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
#image = Image.open("1.jpeg")
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

#Make an array of images, remove for each image the color values outside the threshold
#then save it in a new pdf
def return_cornermarks(img):
    """Return the cornermarks of a PDF using relative positioning

    Parameters
    ----------
    filename : string
        pdf of the file to return the conermarks from
    """
    width, height = img.size
    bounds = [0.1,0.1]
    px = img.load()
    for x in range(int(width*bounds[0]), int(width-width*bounds[0])):
        for y in range(int(height*bounds[1]), int(height-height*bounds[1])):
            px[x,y]=(255,255,255)


def return_answerbox(image):
    """Return the anwerbox of a with the answer blanked out

    Parameters
    ----------
    filename : string
        pdf of the file to return the conermarks from
    """

def conv(img, kernel):
    """Perform convolution of image with a kernel to mimic certain noise effects
    Returns img in grayscale values

    Parameters
    ----------
    img : image
        Image to convolute over
    kernel: numpy array
        kernel to convolute with

    """
    px = img.load()
    width, height = img.size
    kernelDim = int(math.sqrt(kernel.size))
    strideDim = int(kernelDim/2)
    grayscale = np.zeros((width,height))
    out = np.zeros((width,height))
    for x in range(0, width):
        for y in range(0,height):
            grayscale[x,y] = int((sum(px[x,y]))/3)
    for x in range(strideDim, width-strideDim):
        for y in range(strideDim, height-strideDim):
            i = 0
            j = 0
            for k in range(x-strideDim, x+strideDim+1):
                for p in range(y-strideDim, y+strideDim+1):
                    i += grayscale[k,p] * kernel[k+strideDim-x,p+strideDim-y]
            out[x,y] = i
    return Image.fromarray(out).convert("L")


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
            raise RuntimeError(f'Page {pagenr + 1} contains more than 1 image,'
                               'likely not a scan')

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

def testfunc():
    images=[]
    for image, page in extract_images("testpdf.pdf"):
        #image.show()
        return_cornermarks(image)
        rotation = 180+(90-(page%2*180))
        images = images +[image.rotate(rotation, expand=True)]
        #images = images +[image]
        print("page "+str(page)+" is done." )
    #image.show()
    images[0].save("out.pdf", save_all=True, append_images=images[1:])

testfunc()

#print(total)
#enhancer = ImageEnhance.Color(image)
#enhancer2 = ImageEnhance.Contrast(enhancer.enhance(0))
#enhancer2.enhance(1).show()
