"""Generate PDF from images"""
from os import listdir
import img2pdf


def gen_pdf(src: str, dst: str, filename: str):
    """Generate PDF from images in src to dst"""
    filenames = sorted(listdir(src))
    filenames = [f"{src}/{filename}" for filename in filenames]
    with open(f"{dst}/{filename}.pdf", "wb") as ofile:
        ofile.write(img2pdf.convert(filenames))
