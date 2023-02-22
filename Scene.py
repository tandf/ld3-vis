#! /bin/env python3

from __future__ import annotations
from alive_progress import alive_bar
from typing import List, Tuple
import matplotlib.pyplot as plt
import os
import shutil

from Actor import *
from Controller import *
from Point import *

class Camera:
    def __init__(self, get_view: function = None) -> None:
        self._get_view = get_view

    def _follow_ego(self) -> None:
        def get_view(self, ego: Car) -> Rect:
            leftbottom = ego.pos - self.ego_relpos
            righttop = leftbottom + self.limits
            return Rect(leftbottom, righttop)
        self.limits = Point(40, 30)  # meter
        self.ego_relpos = Point(20, 12)  # meter
        self._get_view = get_view

    def _follow_ego_x(self) -> None:
        def get_view(self, ego: Car) -> Rect:
            ego_pos = copy.deepcopy(ego.pos)
            ego_pos.y = self._y
            leftbottom = ego_pos - self.ego_relpos
            righttop = leftbottom + self.limits
            return Rect(leftbottom, righttop)
        self.limits = Point(30, 20)  # meter
        self.ego_relpos = Point(15, 3)  # meter
        self._y = 0
        self._get_view = get_view

    def get_view(self, ego: Actor) -> Rect:
        assert(self._get_view)
        return self._get_view(self, ego)

class Scene:
    actors: ActorList
    ego: Car

    def __init__(self, root_dir: str, name: str, fps: int = 60,
                 speed_factor: float = 1, fig_size: Tuple[int, int] = (8, 6),
                 dpi: int = 100, debug=False):
        self.root_dir = root_dir
        self.pic_dir = os.path.join(root_dir, name)
        self.name = name

        if os.path.isdir(self.pic_dir):
            shutil.rmtree(self.pic_dir)
        os.mkdir(self.pic_dir)

        # Animation setting
        self.speed_factor = speed_factor
        self.fps = fps
        self.cnt = 0
        self.time = 0
        self.view = None
        self.fig_size = fig_size
        self.dpi = dpi

        self.debug = debug

        # Camera setting
        self.camera = Camera()
        self.camera._follow_ego_x()

        # Actors
        self.actors = ActorList()
        self.ego = None

    def set_ego(self, ego: Car) -> None:
        self.ego = ego
        self.camera._y = ego.pos.y

    def add_actor(self, actor: Actor) -> None:
        self.actors.add(actor)

    def plot(self) -> None:
        f = plt.figure(figsize=self.fig_size, dpi=self.dpi)
        plt.xlim(self.view.leftbottom.x, self.view.righttop.x)
        plt.ylim(self.view.leftbottom.y, self.view.righttop.y)
        ax = plt.gca()
        for spine in ax.spines.values():
            spine.set_visible(False)

        self.actors.plot()

        if self.debug:
            plt.title(f"{self.time:.1f} s")
        else:
            ax.get_yaxis().set_visible(False)
            ax.get_xaxis().set_visible(False)
            plt.tight_layout()

        filename = f"{self.cnt:06d}.png"
        f.savefig(os.path.join(self.pic_dir, filename))
        plt.close(f)

    def step(self, time: float = None) -> None:
        if time is not None:
            self.time = time
        else:
            dt = 1 / self.fps * self.speed_factor
            self.time += dt
            self.cnt += 1

        self.view = self.camera.get_view(self.ego)

        self.actors.step(self.time, self.view)

    def run(self, steps: int) -> None:
        self.step(0)  # init

        with alive_bar(steps, title=self.name) as bar:
            for _ in range(steps):
                self.plot()
                self.step()
                bar()

    def to_vid(self, file: str = None) -> None:
        if not file:
            file = os.path.join(self.root_dir, f"{self.name}.mp4")
        print(file)

        cmd = [f"ffmpeg -y",
               f"-framerate {self.fps}",
               f"-i {os.path.join(self.pic_dir, '%06d.png')}",
               f"-c:v libx264",
               f"-profile:v high",
               f"-crf 20",
               f"-pix_fmt yuv420p",
               f"-hide_banner",
               f"-loglevel error",
               f"{file}",
               ]

        os.system(" ".join(cmd))
