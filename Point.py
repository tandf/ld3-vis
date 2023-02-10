from __future__ import annotations
from typing import Tuple
import numpy as np

class Point:
    def __init__(self, x:int, y:int):
        self.x = x
        self.y = y

    def loc(self) -> Tuple[int, int]:
        return (self.x, self.y)

    def in_view(self, view: Tuple) -> bool:
        # view is a tuple of two points: leftbottom and righttop
        left, right = view[0].x, view[1].x
        bottom, top = view[0].y, view[1].y
        return self.x >= left and self.x <= right and self.y >= bottom and \
                self.y <= top

    def __add__(self, another: Point):
        assert isinstance(another, Point)
        return Point(self.x + another.x, self.y + another.y)

    def __sub__(self, another: Point):
        assert isinstance(another, Point)
        return Point(self.x - another.x, self.y - another.y)

    def __str__(self) -> str:
        return f"({self.x}, {self.y})"

    def __repr__(self) -> str:
        return self.__str__()

    @classmethod
    def nd_error(cls, loc: Point, scale: Point):
        x = np.random.normal(loc=loc.x, scale=scale.x)
        y = np.random.normal(loc=loc.y, scale=scale.y)
        return Point(x, y)
