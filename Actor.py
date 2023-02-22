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
import math

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


class PeriodCB(Callback):
    def __init__(self, start_time: float = 0,
                 end_time: float = float("inf")) -> None:
        super().__init__()
        self.start_time = start_time
        self.end_time = end_time
        self.progress = 0

    def step(self, time: float, view: Rect) -> None:
        super().step(time, view)
        self.progress = (self.time - self.start_time) / \
            (self.end_time - self.start_time)
        if self.time > self.end_time:
            self.is_done = True


class FadeInOutCB(PeriodCB):
    def __init__(self, start_time: float = 0, end_time: float = float("inf"),
                 fadein_time: float = 1, fadeout_time: float = 1) -> None:
        super().__init__(start_time, end_time)
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
            self.actor.is_done = True


class TrajAddPosLifecycleCB(PeriodCB):
    actor: Trajectory

    def __init__(self, start_time: float = 0,
                 end_time: float = float("inf")) -> None:
        super().__init__(start_time, end_time)

    def step(self, time: float, view: Rect) -> None:
        super().step(time, view)
        self.actor._should_add_pos = self.time >= self.start_time \
            and self.time <= self.end_time


class TextTypingCB(PeriodCB):
    actor: Text

    def __init__(self, text: str, start_time: float = 0,
                 end_time: float = float("inf")) -> None:
        super().__init__(start_time, end_time)
        self.text = text

    def step(self, time: float, view: Rect) -> None:
        super().step(time, view)

        if self.time >= self.start_time:
            text_length = math.floor(len(self.text) * self.progress)
            text = self.text[:text_length]
            if text and text_length < len(self.text):
                text += "_"
            self.actor.text = text


class ActionCB(Callback):
    def __init__(self, action: callable, action_time: float) -> None:
        super().__init__(0, action_time)
        self.action_time = action_time
        self._action = action

    def _action(self, actor:Actor) -> None:
        return

    def step(self, time: float, view: Rect) -> None:
        super().step(time, view)
        if self.time > self.action_time:
            self._action(self.actor)
            self.is_done = True


class Actor:
    priority: int
    callbacks: List[Callback]  # For actor animation
    time: float
    is_done: bool

    def __init__(self, priority: int = 50) -> None:
        self.priority = priority
        self.callbacks = []
        self.time = 0
        self.view = None
        self.is_done = False
        self.visible = True
        self.alpha = 1

    def add_cb(self, callback: Callback) -> None:
        callback.actor = self
        self.callbacks.append(callback)

    def step(self, time: float, view: Rect) -> None:
        self.time = time
        self.view = view

        for callback in self.callbacks:
            callback.step(time, view)
        self.callbacks = [c for c in self.callbacks if not c.is_done]

    def _plot(self) -> None:
        return

    def plot(self) -> None:
        if self.visible:
            self._plot()

    def done(self) -> bool:
        return self.is_done


class ActorList(Actor):
    actors: List[Actor]

    def __init__(self, priority: int = 50) -> None:
        super().__init__(priority)
        self.actors = []

    def add(self, actor: Actor) -> None:
        self.actors.append(actor)

    def _sort_actors(self) -> None:
        self.actors.sort(key=lambda a: a.priority)

    def step(self, time: float, view: Rect) -> None:
        self._sort_actors()
        super().step(time, view)
        for actor in self.actors:
            actor.step(self.time, self.view)
        self.actors = [a for a in self.actors if not a.done()]

    def _plot(self) -> None:
        super()._plot()
        for actor in self.actors:
            actor.plot()


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
        super()._plot()

        #  plt.scatter(self.pos.x, self.pos.y)
        ax = plt.gca()
        self.attach_texture(ax)


class GetPos:
    def __init__(self) -> None:
        raise("Wrong usage of class GetPos")

    @ classmethod
    def accurate_meas(cls, p: Point, time: float) -> Point:
        return copy.deepcopy(p)

    @ classmethod
    def gausian_meas(cls, loc: Point = None, scale: Point = None) -> Point:
        loc = loc if loc else Point(0, 0)
        scale = scale if scale else Point(0, 0)

        def _gausian_meas(p: Point, time: float) -> Point:
            error = Point.nd_error(loc, scale)
            return p + error
        return _gausian_meas


class Trajectory(Actor):
    trajectory: List[Point]
    ANIMATION_TIME = 1
    MARKER_SIZE = 120

    DEFAULT_MARKER_STYLE = {
        "marker": "+",
        "color": "grey",
        "linewidth": 3,
    }

    DEFAULT_LINE_STYLE = {
        "ls": "--",
        "marker": "None",
        "color": "grey",
    }

    def __init__(self, car: Car, get_pos = None, sample_period: float = 0.05,
                 marker_style: dict = None, line_style: dict = None):
        super().__init__()

        self.trajectory = []
        self.car = car
        self.sample_period = sample_period
        self.last_add_pos_time = 0
        self._should_add_pos = True

        self.marker_style = marker_style if marker_style else copy.deepcopy(
            self.DEFAULT_MARKER_STYLE)
        self.line_style = line_style if line_style else copy.deepcopy(
            self.DEFAULT_LINE_STYLE)

        self._get_pos = get_pos if get_pos else GetPos.accurate_meas

    def _get_pos(self, pos: Point, time: float) -> Point:
        raise Exception("Uninitialized")

    def _create_pos(self) -> Point:
        pos = self._get_pos(copy.deepcopy(self.car.pos), self.time)
        pos.birthday = self.time
        return pos

    def step(self, time: float, view: Rect) -> None:
        super().step(time, view)

        # Remove outdated points
        self._update_pos(self.view)

        if self.time - self.last_add_pos_time >= self.sample_period:
            pos = self._create_pos()
            self.last_add_pos_time += self.sample_period
            if self._should_add_pos:
                self.trajectory.append(pos)

    def _update_pos(self, view: Rect) -> None:
        # Remove trajectories out of view
        first_idx = 0
        for idx, p in enumerate(self.trajectory):
            if p in view:
                first_idx = idx
                break

        self.trajectory = [p for idx, p in enumerate(
            self.trajectory) if idx + 1 >= first_idx]

    def getxy(self, trajectory: List[Point] = None) -> None:
        trajectory = trajectory if trajectory else self.trajectory
        X = [p.x for p in trajectory]
        Y = [p.y for p in trajectory]
        return X, Y

    def _plot(self) -> None:
        super()._plot()

        # Plot dotted lines
        X, Y = self.getxy()
        plt.plot(X, Y, **self.line_style, alpha=self.alpha)

        old_trajectory = [p for p in self.trajectory
                          if self.time - p.birthday > self.ANIMATION_TIME]
        X, Y = self.getxy(old_trajectory)
        plt.scatter(X, Y, s=self.MARKER_SIZE, **self.marker_style, alpha=self.alpha)

        new_trajectory = [p for p in self.trajectory
                          if self.time - p.birthday <= self.ANIMATION_TIME]
        for p in new_trajectory:
            ratio = 1 + 7 * (1 - (self.time - p.birthday) / self.ANIMATION_TIME)
            plt.scatter(p.x, p.y, s=self.MARKER_SIZE *
                        ratio, **self.marker_style, alpha=self.alpha)


class LaneDetection(Actor):
    car: Car

    MARKER_SIZE = 180
    DEFAULT_MARKER_STYLE = {
        "marker": "+",
        "color": "#40E0D0",
    }

    DEFAULT_ARROW_STYLE = {
        "color": "#40E0D0",
        "length_includes_head": True,
        "width": .02,
        "head_width": .3,
        "head_length": .5,
    }

    def __init__(self, car: Car,  lanes: List[float], offset: Point,
                 get_pos: callable = None, marker_style: dict = None,
                 arrow_style: dict = None):
        super().__init__()
        self.car = car
        self.lanes = lanes
        self.offset = offset
        self._get_pos = get_pos if get_pos else GetPos.accurate_meas

        self.marker_style = marker_style if marker_style else copy.deepcopy(
            self.DEFAULT_MARKER_STYLE)
        self.arrow_style = arrow_style if arrow_style else copy.deepcopy(
            self.DEFAULT_ARROW_STYLE)

    def _get_pos(self, pos: Point, time: float) -> Point:
        raise Exception("Uninitialized")

    def find_adjecent_lanes(self, y: float) -> Tuple(float, float):
        bigger = [l for l in self.lanes if l >= y]
        smaller = [l for l in self.lanes if l < y]

        upper_first = min(bigger) if bigger else None
        lower_first = max(smaller) if smaller else None

        return upper_first, lower_first

    def _plot(self) -> None:
        super()._plot()

        upper, lower = self.find_adjecent_lanes(self.car.pos.y)
        mpos = self._get_pos(self.car.pos, self.time) + self.offset

        if upper is not None and lower is not None:
            # Draw marker
            plt.scatter(mpos.x, mpos.y, s=self.MARKER_SIZE,
                        **self.marker_style)

            # TODO: Draw arrows to lane lines
            upper_arrow_y = mpos.y + .5
            lower_arrow_y = mpos.y - .5
            plt.arrow(mpos.x, upper_arrow_y, 0, upper -
                      upper_arrow_y, alpha=self.alpha, **self.arrow_style)
            plt.arrow(mpos.x, lower_arrow_y, 0, lower -
                      lower_arrow_y, alpha=self.alpha, **self.arrow_style)


class Road(Actor):
    def __init__(self):
        super().__init__(1)

        # https://news.osu.edu/slow-down----those-lines-on-the-road-are-longer-than-you-think/
        self.dashed_line = (3, 9)  # 10 feet line with 30 feet space
        self.line_width = .1  # meters

        self.dashed_lines = [2]  # y
        self.solid_lines = [-2, 6]  # y

    def get_lines(self) -> List[float]:
        return self.dashed_lines + self.solid_lines

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
        super()._plot()

        left, right = self.view.leftbottom.x, self.view.righttop.x
        bottom, top = self.view.leftbottom.y, self.view.righttop.y

        for line in self.solid_lines:
            if self.line_in_view(line, top, bottom):
                self.draw_solid_line(line, left, right)

        for line in self.dashed_lines:
            if self.line_in_view(line, top, bottom):
                self.draw_dashed_line(line, left, right)


class Text(Actor):
    DEFAULT_TEXT_STYLE = {
        "color": "#333343",
        "verticalalignment": "center",
        "size": 30,
    }

    def __init__(self, text: str, pos: Point, text_style: dict = None):
        super().__init__(99)

        self.text = text
        self.text_pos = pos
        self.text_style = text_style if text_style else copy.deepcopy(
            self.DEFAULT_TEXT_STYLE)

    def _plot(self) -> None:
        super()._plot()

        pos = self.text_pos + self.view.leftbottom
        plt.text(pos.x, pos.y, self.text, alpha=self.alpha, **self.text_style)


class TrajLegend(Text):
    MARKER_SIZE = 600

    def __init__(self, text: str, pos: Point, text_style: dict = None,
                 marker_style: dict = None):
        text_pos = pos + Point(1, 0)
        super().__init__(text, text_pos, text_style)

        self.marker_pos = pos
        self.marker_style = copy.deepcopy(marker_style) if marker_style else {}
        if "color" not in self.text_style:
            self.text_style["color"] = self.marker_style["color"]

    def _plot(self) -> None:
        super()._plot()

        pos = self.marker_pos + self.view.leftbottom
        plt.scatter(pos.x, pos.y, s=self.MARKER_SIZE, alpha=self.alpha,
                    **self.marker_style)


class TextList(ActorList):
    actors: List[Text]

    TYPING_TIME = 1

    def __init__(self, titles: Tuple[str, float, float, float], pos: Point,
                 typing_effect: bool = True, text_style: dict = None,
                 priority: int = 99) -> None:
        super().__init__(priority)
        self.pos = pos

        for text, start_time, end_time in titles:
            title = Text(text, pos, text_style)
            title.text_style["verticalalignment"] = "top"
            title.text_style["horizontalalignment"] = "left"
            title.text_style["size"] = 40
            if typing_effect:
                title.add_cb(TextTypingCB(text, start_time, min(
                    start_time+self.TYPING_TIME, end_time)))
            title.add_cb(FadeInOutCB(start_time, end_time))
            self.add(title)


class PolyLine(Actor):
    lines: List[Line]

    DEFAULT_LINE_STYLE = {
        "color": "#708090",
        "linewidth": 3,
    }

    DEFAULT_ARROW_STYLE = {
        "length_includes_head": True,
        "width": .02,
        "head_width": .15,
        "head_length": .4,
    }

    def __init__(self, start: Point, deltas: List[Point], duration: float,
                 start_time: float = -1, line_style: dict = None,
                 arrow_style: dict = None, priority: int = 50):
        super().__init__(priority)
        self.start = start
        self.duration = duration
        self.start_time = start_time

        self.percentage = 0

        self.line_style = line_style if line_style else copy.deepcopy(
            self.DEFAULT_LINE_STYLE)
        self.arrow_style = arrow_style if arrow_style else copy.deepcopy(
            self.DEFAULT_ARROW_STYLE)

        self.lines = []
        p = self.start
        for delta in deltas:
            line = Line(p, delta=delta)
            self.lines.append(line)
            p += delta
        self.length = sum([l.length() for l in self.lines])

    def step(self, time: float, view: Rect) -> None:
        super().step(time, view)

        if self.visible and self.start_time == -1:
            self.start_time = self.time

        if self.duration > 0 and self.time >= self.start_time:
            self.percentage = min(
                1, (self.time - self.start_time) / self.duration)
        else:
            self.percentage = 1

    def _plot(self) -> None:
        super()._plot()

        length = self.percentage * self.length
        len_drawn = 0
        # Draw all lines but the last one without arrow
        X, Y = [], []
        arrow_line = None
        for line in self.lines:
            p = line.start + self.view.leftbottom
            X.append(p.x)
            Y.append(p.y)

            if line.length() + len_drawn >= length:
                part = (length - len_drawn) / line.length()
                arrow_line = line.interpolate(part) + self.view.leftbottom
                break
            else:
                len_drawn += line.length()

        #  print(X, Y)
        plt.plot(X, Y, **self.line_style)
        plt.arrow(arrow_line.start.x, arrow_line.start.y, arrow_line.delta.x,
                  arrow_line.delta.y, alpha=self.alpha,
                  **{**self.arrow_style, **self.line_style})
