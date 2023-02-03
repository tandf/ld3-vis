#! /bin/env python3

from __future__ import annotations
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from typing import List, Tuple
import shutil
import os 
from alive_progress import alive_bar
import copy
import numpy as np
import cairosvg
from PIL import Image
from io import BytesIO

dir_path = os.path.dirname(os.path.realpath(__file__))

def load_car_texture(heading: str = "right") -> Image.Image:
    png = cairosvg.svg2png(url="pics/car-top.svg")
    img = Image.open(BytesIO(png))
    if heading == "right":
        img = img.transpose(Image.ROTATE_270)
    else:
        img = img.transpose(Image.ROTATE_90)
    return img


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

    @classmethod
    def nd_error(cls, loc: Point, scale: Point):
        x = np.random.normal(loc=loc.x, scale=scale.x)
        y = np.random.normal(loc=loc.y, scale=scale.y)
        return Point(x, y)


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
        self.speed_factor = .5
        self.fps = 60
        self.cnt = 0
        self.time = 0

        # Camera setting
        self.limits = Point(40, 30)  # meter
        self.ego_relpos = Point(20, 12)  # meter

        # Actors
        self.actors = []

        # Ego vehicle
        self.ego = Car(pos=Point(0, 0), speedx=20)
        self.ego.set_texture(load_car_texture())
        self.actors.append(self.ego)

        # Real trajectory of ego vehicle
        self.actors.append(Trajectory(self.ego, lambda x: x))

        # GPS measurement of ego vehicle (add normal distribution errors)
        def gps_sampling(x: Point):
            return x + Point.nd_error(Point(0, 0), Point(.5, .5))
        gps_meas = Trajectory(self.ego, gps_sampling, .3)
        gps_meas.marker_style["color"] = "green"
        gps_meas.line_style["color"] = "green"
        self.actors.append(gps_meas)

        # NPC car
        npc = Car(pos=Point(20, 4), speedx=-10)
        npc.set_texture(load_car_texture(heading="left"))
        self.actors.append(npc)

        # Add road
        self.actors.append(Road())

    def get_leftbottom(self) -> Point:
        return self.ego.pos - self.ego_relpos

    def plot(self) -> None:
        leftbottom = self.get_leftbottom()
        righttop = leftbottom + self.limits

        f = plt.figure(figsize=(8, 6), dpi=100)
        plt.xlim(leftbottom.x, righttop.x)
        plt.ylim(leftbottom.y, righttop.y)
        ax = plt.gca()
        #  ax.get_yaxis().set_visible(False)
        for spine in ax.spines.values():
            spine.set_visible(False)
        #  plt.tight_layout()

        for actor in self.actors:
            actor.plot(view=(leftbottom, righttop))

        filename = f"{self.cnt:06d}.png"
        f.savefig(os.path.join(self.out_dir, filename))
        plt.close(f)

    def step(self) -> None:
        dt = 1 / self.fps * self.speed_factor

        for actor in self.actors:
            actor.step(dt)

        # Finishing
        self.time += dt
        self.cnt += 1


class Car(Actor):
    def __init__(self, speedx: int = 0, speedy: int = 0, pos: Point = None):
        self.xspeed = speedx  # m/s
        self.yspeed = speedy  # m/s
        self.pos = pos if pos else Point(0, 0)

        self.texture = None

    def set_texture(self, texture: Image.Image):
        self.texture = texture

    def step(self, dt: float) -> None:
        delta = Point(dt*self.xspeed, dt*self.yspeed)
        self.pos += delta

    def in_view(self, view: Tuple[Point, Point]) -> bool:
        # TODO: Check based on the dimensions of the car
        return True

    def plot(self, view: Tuple[Point, Point]) -> None:
        if self.in_view(view):
            #  plt.scatter(self.pos.x, self.pos.y)
            ax = plt.gca()
            if self.texture:
                ax.imshow(self.texture, extent=(self.pos.x - 2,
                          self.pos.x + 2, self.pos.y - 1.5, self.pos.y + 1.5))


class Trajectory(Actor):
    trajectory: List[Point]
    ANIMATION_FRAME = 20
    MARKER_SIZE = 60

    DEFAULT_MARKER_STYLE = {
        "marker": "+",
        "color": "grey",
    }

    DEFAULT_LINE_STYLE = {
        "ls": ":",
        "marker": "None",
        "color": "grey",
    }

    def __init__(self, car: Car, get_pos_cb, sample_period: float = 0.1,
                 marker_style: dict = None, line_style: dict = None):
        self.trajectory = []
        self.car = car
        self.sample_period = sample_period
        self.time = 0

        self.marker_style = marker_style if marker_style else copy.deepcopy(
            self.DEFAULT_MARKER_STYLE)
        self.line_style = line_style if line_style else copy.deepcopy(
            self.DEFAULT_LINE_STYLE)

        self._get_pos_callback = get_pos_cb

    def _get_pos_callback(self, pos: Point) -> Point:
        raise Exception("Uninitialized")

    def _add_pos(self) -> None:
        pos = self._get_pos_callback(copy.deepcopy(self.car.pos))
        pos.frame_cnt = 0
        self.trajectory.append(pos)

    def step(self, dt: float) -> None:
        self.time += dt
        if self.time >= self.sample_period:
            self._add_pos()
            self.time -= self.sample_period

    def _update_pos(self, view: Tuple[Point, Point]) -> None:
        # Remove trajectories out of view
        first_idx = 0
        for idx, p in enumerate(self.trajectory):
            if p.in_view(view):
                first_idx = idx
                break

        self.trajectory = [p for idx, p in enumerate(
            self.trajectory) if idx + 1 >= first_idx]
        for p in self.trajectory:
            p.frame_cnt += 1

    def getxy(self, trajectory: List[Point] = None) -> None:
        trajectory = trajectory if trajectory else self.trajectory
        X = [p.x for p in trajectory]
        Y = [p.y for p in trajectory]
        return X, Y

    def plot(self, view: Tuple[Point, Point]) -> None:
        # Remove outdated points
        self._update_pos(view)

        # Plot dotted lines
        X, Y = self.getxy()
        plt.plot(X, Y, **self.line_style)

        old_trajectory = [p for p in self.trajectory
                          if p.frame_cnt > self.ANIMATION_FRAME]
        X, Y = self.getxy(old_trajectory)
        plt.scatter(X, Y, s=self.MARKER_SIZE, **self.marker_style)

        new_trajectory = [p for p in self.trajectory
                          if p.frame_cnt <= self.ANIMATION_FRAME]
        for p in new_trajectory:
            frame_cnt = p.frame_cnt
            ratio = 1 + 7 * (1 - frame_cnt/self.ANIMATION_FRAME)
            plt.scatter(p.x, p.y, s=self.MARKER_SIZE * ratio, **self.marker_style)

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
    steps = 500
    with alive_bar(steps) as bar:
        for i in range(steps):
            scene.plot()
            scene.step()
            bar()
