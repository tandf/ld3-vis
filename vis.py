#! /bin/env python3

from __future__ import annotations
from PIL import Image
from alive_progress import alive_bar
from io import BytesIO
from typing import List, Tuple
import cairosvg
import matplotlib.pyplot as plt
import os
import shutil

from Point import Point
from Actor import *
from Controller import *

dir_path = os.path.dirname(os.path.realpath(__file__))


def load_car_texture(heading: str = "right") -> Image.Image:
    png = cairosvg.svg2png(url="pics/car-top.svg")
    img = Image.open(BytesIO(png))
    if heading == "right":
        img = img.transpose(Image.ROTATE_270)
    else:
        img = img.transpose(Image.ROTATE_90)
    return img


class Scene:
    actors: List[Actor]

    def __init__(self, out_dir=os.path.join(dir_path, "out"), fps: int = 60,
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
        self.limits = Point(40, 30)  # meter
        self.ego_relpos = Point(20, 12)  # meter

        # Actors
        self.actors = []

        # Ego vehicle
        egoController = PIDController(Point(20, 0), yref=0)
        self.ego = Car(pos=Point(0, 0), controller=egoController)
        self.ego.set_texture(load_car_texture())
        self.actors.append(self.ego)

        # Real trajectory of ego vehicle
        self.actors.append(Trajectory(self.ego, lambda x: x, self.fps))

        # GPS measurement of ego vehicle (add normal distribution errors)
        def gps_sampling(x: Point):
            return x + Point.nd_error(Point(0, 0), Point(.5, .5))
        gps_meas = Trajectory(self.ego, gps_sampling, self.fps, .3)
        gps_meas.marker_style["color"] = "green"
        gps_meas.line_style["color"] = "green"
        self.actors.append(gps_meas)
        egoController.traj = gps_meas

        # NPC car
        npc = Car(pos=Point(20, 4),
                  controller=Controller(Point(-10, 0)))
        npc.set_texture(load_car_texture(heading="left"))
        self.actors.append(npc)

        # Add road
        self.actors.append(Road())

        self.actors.sort(key=lambda a: a.priority)

    def get_leftbottom(self) -> Point:
        return self.ego.pos - self.ego_relpos

    def plot(self) -> None:
        leftbottom = self.get_leftbottom()
        righttop = leftbottom + self.limits

        f = plt.figure(figsize=self.fig_size, dpi=self.dpi)
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


if __name__ == "__main__":
    steps = 100
    fps = 10
    dpi = 100
    out_dir = os.path.join(dir_path, "out")

    scene = Scene(out_dir, fps, dpi=dpi)
    with alive_bar(steps) as bar:
        for i in range(steps):
            scene.plot()
            scene.step()
            bar()

    cmd = [f"ffmpeg -y",
           f"-framerate {fps}",
           f"-i {os.path.join(out_dir, '%06d.png')}",
           f"-c:v libx264",
           f"-profile:v high",
           f"-crf 20",
           f"-pix_fmt yuv420p",
           f"-hide_banner",
           f"-loglevel error",
           f"out.mp4",
           ]

    os.system(" ".join(cmd))
