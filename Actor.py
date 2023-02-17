from __future__ import annotations
from PIL import Image
from io import BytesIO
from matplotlib.patches import Rectangle
from scipy import ndimage
from typing import List
import cairosvg
import copy
import matplotlib.pyplot as plt
import numpy as np

from Point import *


class Callback:
    actor: Actor

    def __init__(self) -> None:
        self.actor = None
        self.time = 0
        self.view = Rect(Point(0, 0), Point(0, 0))
        self.is_done = False

    def step(self, time: float, view: Rect) -> None:
        self.time = time
        self.view = view

class DeleteAfterDisappearCB(Callback):
    def __init__(self) -> None:
        super().__init__()
        self.in_once = False

    def step(self, time: float, view: Rect) -> None:
        super().step(time, view)

        if self.actor.visible:
            self.in_once = True
        elif self.in_once:
            self.is_done = True
            self.actor.is_done = True


class FadeInOutCB(Callback):
    def __init__(self, start_time: float = 0, end_time: float = float("inf"),
                 fadein_time: float = 1, fadeout_time: float = 1) -> None:
        super().__init__()
        self.start_time = start_time
        self.end_time = end_time
        self.fadein_time = fadein_time
        self.fadeout_time = fadeout_time

    def step(self, time: float, view: Rect) -> None:
        super().step(time, view)
        self.actor.alpha = min(
            (self.time - self.start_time) / self.fadein_time,
            (self.end_time - self.time) / self.fadeout_time,
            1)

        self.actor.visible = self.time >= self.start_time \
            and self.time <= self.end_time
        if self.time > self.end_time:
            self.is_done = True
            self.actor.is_done = True


class Actor:
    priority: int
    callbacks: List[Callback]  # For actor animation
    time: float
    is_done: bool

    def __init__(self, priority: int = 50):
        self.priority = priority
        self.callbacks = []
        self.time = 0
        self.view = None
        self.is_done = False
        self.visible = True

    def add_cb(self, callback: Callback) -> None:
        callback.actor = self
        self.callbacks.append(callback)

    def step(self, time: float, view: Rect):
        self.time = time
        self.view = view

        for callback in self.callbacks:
            callback.step(time, view)
        self.callbacks = [c for c in self.callbacks if not c.is_done]

    def _plot(self) -> None:
        raise Exception("Uninitialized")

    def plot(self) -> None:
        if self.visible:
            self._plot()

    def done(self) -> bool:
        return self.is_done


class Car(Actor):
    def __init__(self, controller, pos: Point = None, appear_once = True):
        super().__init__(90)

        self.controller = controller
        self.pos = pos if pos else Point(0, 0)
        self.direction = 0

        self.texture = None
        self.texture_rotate = False

        if appear_once:
            self.add_cb(DeleteAfterDisappearCB())

    def load_texture(self, file: str = "pics/car-top.svg",
                     heading: str = "right") -> Image.Image:
        png = cairosvg.svg2png(url=file)
        img = Image.open(BytesIO(png))
        if heading == "right":
            img = img.transpose(Image.ROTATE_270)
        else:
            img = img.transpose(Image.ROTATE_90)
        self.texture = img

    def step(self, time: float, view: Rect) -> None:
        dt = time - self.time
        self.visible = self.in_view(view)

        super().step(time, view)

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

    def _plot(self) -> None:
        #  plt.scatter(self.pos.x, self.pos.y)
        ax = plt.gca()
        self.attach_texture(ax)


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
        self.alpha = 1

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

    def step(self, time: float, view: Rect) -> None:
        super().step(time, view)

        # Remove outdated points
        self._update_pos(self.view)

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

    def _plot(self) -> None:
        # Plot dotted lines
        X, Y = self.getxy()
        plt.plot(X, Y, **self.line_style, alpha=self.alpha)

        old_trajectory = [p for p in self.trajectory
                          if p.frame_cnt / self.fps > self.ANIMATION_TIME]
        X, Y = self.getxy(old_trajectory)
        plt.scatter(X, Y, s=self.MARKER_SIZE, **self.marker_style, alpha=self.alpha)

        new_trajectory = [p for p in self.trajectory
                          if p.frame_cnt / self.fps <= self.ANIMATION_TIME]
        for p in new_trajectory:
            frame_cnt = p.frame_cnt
            ratio = 1 + 7 * (1 - frame_cnt / self.fps / self.ANIMATION_TIME)
            plt.scatter(p.x, p.y, s=self.MARKER_SIZE *
                        ratio, **self.marker_style, alpha=self.alpha)


class Road(Actor):
    def __init__(self):
        super().__init__(1)

        # https://news.osu.edu/slow-down----those-lines-on-the-road-are-longer-than-you-think/
        self.dashed_line = (3, 9)  # 10 feet line with 30 feet space
        self.line_width = .1  # meters

        self.dashed_lines = [2]  # y
        self.solid_lines = [-2, 6]  # y

    def step(self, time: float, view: Rect) -> None:
        super().step(time, view)

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

    def _plot(self) -> None:
        left, right = self.view.leftbottom.x, self.view.righttop.x
        bottom, top = self.view.leftbottom.y, self.view.righttop.y

        for line in self.solid_lines:
            if self.line_in_view(line, top, bottom):
                self.draw_solid_line(line, left, right)

        for line in self.dashed_lines:
            if self.line_in_view(line, top, bottom):
                self.draw_dashed_line(line, left, right)


class Text(Actor):
    FONT_SIZE = 14

    def __init__(self, text: str, pos: Point, text_style: dict = None):
        super().__init__(99)

        self.text = text
        self.text_pos = pos
        self.text_style = text_style if text_style else {}

        self.time = 0
        self.alpha = 1

    def step(self, time: float, view: Rect) -> None:
        super().step(time, view)

    def _plot(self) -> None:
        pos = self.text_pos + self.view.leftbottom
        plt.text(pos.x, pos.y, self.text, verticalalignment="center",
                 alpha=self.alpha, size=self.FONT_SIZE, **self.text_style)


class TrajLegend(Text):
    MARKER_SIZE = 100

    def __init__(self, text: str, pos: Point, text_style: dict = None,
                 marker_style: dict = None):
        text_pos = pos + Point(1, 0)
        super().__init__(text, text_pos, text_style)

        self.marker_pos = pos
        self.marker_style = marker_style if marker_style else {}

    def step(self, time: float, view: Rect) -> None:
        super().step(time, view)

    def _plot(self) -> None:
        super()._plot()
        pos = self.marker_pos + self.view.leftbottom
        plt.scatter(pos.x, pos.y, s=120, alpha=self.alpha,
                    **self.marker_style)
