from __future__ import annotations
from typing import Tuple
import numpy as np

class Point:
    def __init__(self, x:int, y:int):
        self.x = x
        self.y = y

    def loc(self) -> Tuple[int, int]:
        return (self.x, self.y)

    def __add__(self, another: Point) -> Point:
        assert isinstance(another, Point)
        return Point(self.x + another.x, self.y + another.y)

    def __sub__(self, another: Point) -> Point:
        assert isinstance(another, Point)
        return Point(self.x - another.x, self.y - another.y)

    def __mul__(self, factor: float) -> Point:
        return Point(self.x * factor, self.y * factor)

    def __str__(self) -> str:
        return f"({self.x}, {self.y})"

    def __repr__(self) -> str:
        return self.__str__()

    @classmethod
    def nd_error(cls, loc: Point, scale: Point):
        x = np.random.normal(loc=loc.x, scale=scale.x)
        y = np.random.normal(loc=loc.y, scale=scale.y)
        return Point(x, y)

class Rect:
    def __init__(self, leftbottom:Point, righttop:Point) -> None:
        self.leftbottom = leftbottom
        self.righttop = righttop

    def __contains__(self, p: Point) -> bool:
        assert(isinstance(p, Point))
        return p.x > self.leftbottom.x and p.x < self.righttop.x and \
                p.y > self.leftbottom.y and p.y < self.righttop.y
