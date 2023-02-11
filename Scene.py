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
            if not self._y:
                self._y = ego_pos.y
            ego_pos.y = self._y
            leftbottom = ego_pos - self.ego_relpos
            righttop = leftbottom + self.limits
            return Rect(leftbottom, righttop)
        self.limits = Point(40, 30)  # meter
        self.ego_relpos = Point(20, 12)  # meter
        self._y = None
        self._get_view = get_view

    def get_view(self, ego: Actor) -> Rect:
        assert(self._get_view)
        return self._get_view(self, ego)

class Scene:
    actors: List[Actor]
    ego: Car

    def __init__(self, out_dir, fps: int = 60,
                 fig_size: Tuple[int, int] = (8, 6), dpi: int = 100):
        self.out_dir = out_dir

        if os.path.isdir(self.out_dir):
            shutil.rmtree(self.out_dir)
        os.mkdir(self.out_dir)

        # Animation setting
        self.speed_factor = .5
        self.fps = fps
        self.cnt = 0
        self.time = 0
        self.fig_size = fig_size
        self.dpi = dpi

        # Camera setting
        self.camera = Camera()
        self.camera._follow_ego_x()

        # Actors
        self.actors = []
        self.ego = None

    def add_actor(self, actor: Actor) -> None:
        self.actors.append(actor)

    def sort_actors(self) -> None:
        self.actors.sort(key=lambda a: a.priority)

    def plot(self) -> None:
        view = self.camera.get_view(self.ego)

        f = plt.figure(figsize=self.fig_size, dpi=self.dpi)
        plt.xlim(view.leftbottom.x, view.righttop.x)
        plt.ylim(view.leftbottom.y, view.righttop.y)
        ax = plt.gca()
        #  ax.get_yaxis().set_visible(False)
        for spine in ax.spines.values():
            spine.set_visible(False)
        #  plt.tight_layout()

        for actor in self.actors:
            actor.plot(view=view)

        filename = f"{self.cnt:06d}.png"
        f.savefig(os.path.join(self.out_dir, filename))
        plt.close(f)

    def step(self) -> None:
        dt = 1 / self.fps * self.speed_factor

        for actor in self.actors:
            actor.step(dt)
        self.actors = [a for a in self.actors if not a.done()]

        # Finishing
        self.time += dt
        self.cnt += 1

    def run(self, steps: int) -> None:
        with alive_bar(steps) as bar:
            for i in range(steps):
                self.plot()
                self.step()
                bar()

    def to_vid(self, file: str) -> None:
        cmd = [f"ffmpeg -y",
               f"-framerate {self.fps}",
               f"-i {os.path.join(self.out_dir, '%06d.png')}",
               f"-c:v libx264",
               f"-profile:v high",
               f"-crf 20",
               f"-pix_fmt yuv420p",
               f"-hide_banner",
               f"-loglevel error",
               f"{file}",
               ]

        os.system(" ".join(cmd))
