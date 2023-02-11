from __future__ import annotations
from PIL import Image
from io import BytesIO
from matplotlib.patches import Rectangle
from scipy import ndimage
from typing import Tuple, List
import cairosvg
import copy
import matplotlib.pyplot as plt
import numpy as np

from Point import *


class Actor:
    priority: int

    def __init__(self, priority: int = 50):
        self.priority = priority

    def step(self, dt: float):
        raise Exception("Uninitialized")

    def plot(self, view: Rect):
        raise Exception("Uninitialized")

    def done(self) -> bool:
        return False


class Car(Actor):
    def __init__(self, controller, pos: Point = None):
        super().__init__(99)

        self.controller = controller
        self.pos = pos if pos else Point(0, 0)
        self.direction = 0

        self.texture = None
        self.texture_rotate = False

        self.in_once = False
        self.is_done = False

    def load_texture(self, file: str = "pics/car-top.svg",
                     heading: str = "right") -> Image.Image:
        png = cairosvg.svg2png(url=file)
        img = Image.open(BytesIO(png))
        if heading == "right":
            img = img.transpose(Image.ROTATE_270)
        else:
            img = img.transpose(Image.ROTATE_90)
        self.texture = img

    def step(self, dt: float) -> None:
        speed = self.controller.get_speed()
        assert speed, "Uninitialized controller!"
        if speed.x > 30:
            speed.x = 30
        if speed.x < -30:
            speed.x = -30
        if speed.y > 5:
            speed.y = 5
        if speed.y < -5:
            speed.y = -5
        self.pos += speed * dt
        self.direction = np.arctan2(speed.y, speed.x) / np.pi * 180

    def get_rect(self) -> Rect:
        leftbottom = Point(self.pos.x - 2, self.pos.y - 1.5)
        righttop = Point(self.pos.x + 2, self.pos.y + 1.5)
        return Rect(leftbottom, righttop)

    def in_view(self, view: Rect) -> bool:
        rect = self.get_rect()
        return rect.leftbottom in view or rect.righttop in view

    def attach_texture(self, ax) -> None:
        if not self.texture:
            return

        if self.texture_rotate:
            # TODO: get the correct extent
            texture = ndimage.rotate(self.texture, self.direction)
        else:
            texture = self.texture

        rect = self.get_rect()
        ax.imshow(texture, extent=(rect.leftbottom.x,
                  rect.righttop.x, rect.leftbottom.y, rect.righttop.y))

    def plot(self, view: Rect) -> None:
        if self.in_view(view):
            #  plt.scatter(self.pos.x, self.pos.y)
            self.in_once = True
            ax = plt.gca()
            self.attach_texture(ax)
        elif self.in_once:
            self.is_done = True

    def done(self) -> bool:
        return self.is_done


class Trajectory(Actor):
    trajectory: List[Point]
    ANIMATION_TIME = 1
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

    def __init__(self, car: Car, get_pos_cb, fps: int, sample_period: float = 0.05,
                 marker_style: dict = None, line_style: dict = None):
        super().__init__()

        self.trajectory = []
        self.car = car
        self.fps = fps
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

    def _update_pos(self, view: Rect) -> None:
        # Remove trajectories out of view
        first_idx = 0
        for idx, p in enumerate(self.trajectory):
            if p in view:
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

    def plot(self, view: Rect) -> None:
        # Remove outdated points
        self._update_pos(view)

        # Plot dotted lines
        X, Y = self.getxy()
        plt.plot(X, Y, **self.line_style)

        old_trajectory = [p for p in self.trajectory
                          if p.frame_cnt / self.fps > self.ANIMATION_TIME]
        X, Y = self.getxy(old_trajectory)
        plt.scatter(X, Y, s=self.MARKER_SIZE, **self.marker_style)

        new_trajectory = [p for p in self.trajectory
                          if p.frame_cnt / self.fps <= self.ANIMATION_TIME]
        for p in new_trajectory:
            frame_cnt = p.frame_cnt
            ratio = 1 + 7 * (1 - frame_cnt / self.fps / self.ANIMATION_TIME)
            plt.scatter(p.x, p.y, s=self.MARKER_SIZE *
                        ratio, **self.marker_style)


class Road(Actor):
    def __init__(self):
        super().__init__(1)

        # https://news.osu.edu/slow-down----those-lines-on-the-road-are-longer-than-you-think/
        self.dashed_line = (3, 9)  # 10 feet line with 30 feet space
        self.line_width = .1  # meters

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

    def draw_dashed_line(self, line: float, left: float, right: float) -> None:
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

    def plot(self, view: Rect) -> None:
        left, right = view.leftbottom.x, view.righttop.x
        bottom, top = view.leftbottom.y, view.righttop.y

        for line in self.solid_lines:
            if self.line_in_view(line, top, bottom):
                self.draw_solid_line(line, left, right)

        for line in self.dashed_lines:
            if self.line_in_view(line, top, bottom):
                self.draw_dashed_line(line, left, right)
