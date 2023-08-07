"""Convert images"""
from os import listdir
from PIL import Image


class Converter:
    """Convert images"""

    def __init__(self, path: str = "output/tmp/", change_decode: bool = False) -> None:
        self.path = path
        self.change_decode = change_decode
        self.doc_id_threshold = 158295

    def new_convert(self, filename: str, doc_id: int, page_num: int) -> None:
        """Convert image using the new method"""
        img = Image.open(f"{self.path}/{filename}")
        new_img = Image.new(img.mode, img.size)
        width, height = img.size[0] // 3, img.size[1] // 3

        img_hashmap_x = [1, 2, 0, 0, 1, 2, 2, 0, 1]
        img_hashmap_y = [2, 0, 1, 0, 1, 2, 1, 2, 0]
        offset = doc_id * 5 + page_num * 4

        for i in range(9):
            loc_x = img_hashmap_x[(i + offset) % 9] * width
            loc_y = img_hashmap_y[(i + offset) % 9] * height
            region = img.crop((loc_x, loc_y, loc_x + width, loc_y + height))
            new_img.paste(region, ((i % 3) * width, (i // 3) * height))

        new_img.save(f"{self.path}/{filename}")

    def old_convert(self, filename: str) -> None:
        """Convert image using the old method"""
        img = Image.open(f"{self.path}/{filename}")
        new_img = Image.new(img.mode, img.size)
        width, height = img.size[0] // 3, img.size[1] // 3

        img_hashmap_x = [1, 0, 2]
        img_hashmap_y = [2, 0, 1]

        for i in range(9):
            loc_x, loc_y = (i % 3) * width, (i // 3) * height
            out_x, out_y = img_hashmap_x[i % 3] * width, img_hashmap_y[i // 3] * height
            box = (loc_x, loc_y, loc_x + width, loc_y + height)
            region = img.crop(box)
            new_img.paste(region, (out_x, out_y))

        new_img.save(f"{self.path}/{filename}")

    def convert(self, doc_id: int) -> None:
        """Conver files in `path`"""
        pages = sorted(listdir(self.path))
        for page in pages:
            if (doc_id < self.doc_id_threshold) ^ self.change_decode:
                self.old_convert(page)
            else:
                page_num = int(page[: page.find(".jpg")])
                self.new_convert(page, doc_id, page_num)
