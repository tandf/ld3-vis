#! /bin/env python3

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from typing import List, Tuple
import shutil
import os 
from alive_progress import alive_bar

dir_path = os.path.dirname(os.path.realpath(__file__))

class Point:
    def __init__(self, x:int, y:int):
        self.x = x
        self.y = y

    def loc(self) -> Tuple[int, int]:
        return (self.x, self.y)

    def __add__(self, another):
        assert isinstance(another, Point)
        return Point(self.x + another.x, self.y + another.y)

    def __sub__(self, another):
        assert isinstance(another, Point)
        return Point(self.x - another.x, self.y - another.y)

    def __str__(self) -> str:
        return f"({self.x}, {self.y})"


class Actor:
    def __init__(self):
        pass

    def step(self, dt: float):
        raise Exception("Uninitialized")

    def plot(self, view:Tuple[Point, Point]):
        raise Exception("Uninitialized")


class Scene:
    actors: List[Actor]

    def __init__(self, out_dir=os.path.join(dir_path, "out")):
        self.out_dir = out_dir

        if os.path.isdir(self.out_dir):
            shutil.rmtree(self.out_dir)
        os.mkdir(self.out_dir)

        # Animation setting
        self.speed_rate = .5
        self.fps = 60
        self.cnt = 0
        self.time = 0

        # Camera setting
        self.limits = Point(15, 15)  # meter
        self.ego_relpos = Point(4, 5)  # meter

        # Actors
        self.actors = []
        self.ego = Ego()
        self.actors.append(self.ego)
        self.actors.append(Road())

    def get_leftbottom(self) -> Point:
        return self.ego.pos - self.ego_relpos

    def plot(self) -> None:
        leftbottom = self.get_leftbottom()
        righttop = leftbottom + self.limits

        f = plt.figure()
        plt.xlim(leftbottom.x, righttop.x)
        plt.ylim(leftbottom.y, righttop.y)
        #  plt.tight_layout()

        for actor in self.actors:
            actor.plot(view=(leftbottom, righttop))

        filename = f"{self.cnt:06d}.png"
        f.savefig(os.path.join(self.out_dir, filename))
        plt.close(f)

    def step(self) -> None:
        dt = 1 / self.fps * self.speed_rate

        for actor in self.actors:
            actor.step(dt)

        # Finishing
        self.time += dt
        self.cnt += 1


class Ego(Actor):
    def __init__(self):
        self.xspeed = 20  # m/s
        self.yspeed = 0  # m/s
        self.pos = Point(0, 0)

    def step(self, dt: float) -> None:
        delta = Point(dt*self.xspeed, dt*self.yspeed)
        self.pos += delta

    def plot(self, view: Tuple[Point, Point]) -> None:
        plt.scatter(self.pos.x, self.pos.y)


class Road(Actor):
    def __init__(self):
        # https://news.osu.edu/slow-down----those-lines-on-the-road-are-longer-than-you-think/
        self.dashed_line = (3, 9)  # 10 feet line with 30 feet space
        self.line_width = .1 # meters

        self.dashed_lines = [2]  # y
        self.solid_lines = [-2, 6]  # y

    def step(self, dt: float) -> None:
        pass  # Lane lines don't move

    def line_in_view(self, y: float, top: float, bottom: float) -> bool:
        return (y - self.line_width/2 < top) and (y + self.line_width/2 > bottom)

    def draw_solid_line(self, line: float, left: float, right: float) -> None:
        ax = plt.gca()
        ax.add_patch(Rectangle((left, line-self.line_width/2),
                     right - left, self.line_width))

    def draw_dashed_line(self, line:float, left:float, right:float) -> None:
        start = left
        ax = plt.gca()

        segment_length = sum(self.dashed_line)
        start = segment_length * int(left / segment_length)

        while start <= right:
            end = start + self.dashed_line[0]
            if start < left:
                start = left
            if end > right:
                end = right
            ax.add_patch(Rectangle((start, line-self.line_width/2),
                         end - start, self.line_width))
            start = end + self.dashed_line[1]

    def plot(self, view: Tuple[Point, Point]) -> None:
        left, right = view[0].x, view[1].x
        bottom, top = view[0].y, view[1].y

        for line in self.solid_lines:
            if self.line_in_view(line, top, bottom):
                self.draw_solid_line(line, left, right)

        for line in self.dashed_lines:
            if self.line_in_view(line, top, bottom):
                self.draw_dashed_line(line, left, right)

if __name__ == "__main__":
    scene = Scene()
    steps = 30
    with alive_bar(steps) as bar:
        for i in range(steps):
            scene.plot()
            scene.step()
            bar()
