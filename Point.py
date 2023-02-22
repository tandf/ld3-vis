from __future__ import annotations
from typing import Tuple
import numpy as np


class Point:
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y

    def loc(self) -> Tuple[int, int]:
        return (self.x, self.y)

    def dis(self, __o: Point) -> float:
        assert(isinstance(__o, Point))
        return np.sqrt((self.x - __o.x) ** 2 + (self.y - __o.y) ** 2)

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
    

class Line:
    start: Point
    end: Point

    def __init__(self, start: Point, end: Point = None,
                 delta: Point = None) -> None:
        self.start = start
        assert bool(end) != bool(delta)
        self.end = end if end else self.start + delta
        self.delta = self.start - self.end

    def __add__(self, shift: Point) -> Line:
        return Line(self.start + shift, self.end + shift)

    def __sub__(self, shift: Point) -> Line:
        return Line(self.start - shift, self.end - shift)

    def __str__(self) -> str:
        return f"{self.start}->{self.end}"

    def __repr__(self) -> str:
        return self.__str__()

    def length(self) -> float:
        return self.start.dis(self.end)

    def interpolate(self, percentage: float) -> Line:
        return Line(self.start, delta=self.delta*percentage)


class Rect:
    def __init__(self, leftbottom: Point, righttop: Point) -> None:
        self.leftbottom = leftbottom
        self.righttop = righttop

    def __contains__(self, p: Point) -> bool:
        assert(isinstance(p, Point))
        return p.x > self.leftbottom.x and p.x < self.righttop.x and \
            p.y > self.leftbottom.y and p.y < self.righttop.y
