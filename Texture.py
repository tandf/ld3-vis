from __future__ import annotations
import os
from scipy import ndimage
import cairosvg
from PIL import Image
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from io import BytesIO
import numpy as np
import copy

from Point import Rect


class Texture:
    img: np.array

    IMAGE_STYLE = {
        "zorder": 10,
    }

    def __init__(self, file: str, rotate: int = None,
                 rotate_degree: float = None,
                 image_style: dict = None) -> None:
        self.file = file
        self.img = None
        self._load_texture()
        self.image_style = image_style if image_style else copy.deepcopy(
            self.IMAGE_STYLE)

        if rotate is not None:
            self.rotate90(rotate)
        if rotate_degree is not None:
            self.rotate(rotate_degree)

        self.img_original = copy.deepcopy(self.img)

    def _load_texture(self) -> None:
        ext = os.path.splitext(self.file)[1]
        if ext == ".svg":
            png = cairosvg.svg2png(url=self.file)
            img = Image.open(BytesIO(png))
            self.img_original = np.array(img)
        elif ext == ".png":
            self.img_original = mpimg.imread(self.file)
        else:
            raise Exception(f"Unsupported texture type: {ext}")
        self.img = copy.deepcopy(self.img_original)

    def rotate90(self, k: int) -> None:
        self.img = np.rot90(self.img, k)

    def rotate(self, degree: float) -> None:
        self.img = ndimage.rotate(self.img, degree)
        self.img = np.clip(self.img, 0, 1)

    def rotate_to(self, degree: float) -> None:
        self.img = ndimage.rotate(self.img_original, degree)
        self.img = np.clip(self.img, 0, 1)

    def draw(self, rect: Rect) -> None:
        plt.gca().imshow(self.img, extent=(rect.leftbottom.x, rect.righttop.x,
                                           rect.leftbottom.y, rect.righttop.y),
                         **self.image_style)
