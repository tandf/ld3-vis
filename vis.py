#! /bin/env python3

from __future__ import annotations
import os

from Scene import Scene
from Point import Point
from Actor import *
from Controller import *


dir_path = os.path.dirname(os.path.realpath(__file__))


def attack(debug:bool=False):
    fps = 10 if debug else 60
    dpi = 100
    steps = 30 if debug else 500
    out_dir = os.path.join(dir_path, "attack")

    scene = Scene(out_dir, fps, dpi=dpi, debug=debug)

    # Add road
    scene.add_actor(Road())

    # NPC car
    npc = Car(pos=Point(30, 4),
              controller=Controller(Point(-10, 0)))
    npc.load_texture(heading="left")
    scene.add_actor(npc)

    # Ego vehicle
    egoController = PIDController(Point(20, 0), yref=0)
    scene.set_ego(Car(pos=Point(0, 0), controller=egoController))
    scene.ego.load_texture()
    scene.add_actor(scene.ego)

    # Real trajectory of ego vehicle
    real_meas = Trajectory(scene.ego, lambda x: x, scene.fps)
    real_meas.MARKER_SIZE = 10
    scene.add_actor(real_meas)

    # Attacker measurement
    class Attack:
        def __init__(self, yinit: int):
            self.y = yinit
            self.dy = -0.05
        def __call__(self, p: Point) -> Point:
            self.y += self.dy
            self.dy *= 1.1
            return Point(p.x, self.y)
    attack_meas = Trajectory(scene.ego, Attack(0), scene.fps, .1)
    attack_meas.marker_style["color"] = "red"
    attack_meas.line_style["color"] = "red"
    scene.add_actor(attack_meas)
    egoController.traj = attack_meas

    scene.run(steps)
    scene.to_vid("attack.mp4")

def benign(debug:bool=False):
    fps = 10 if debug else 60
    dpi = 100
    steps = 30 if debug else 500
    out_dir = os.path.join(dir_path, "benign")

    scene = Scene(out_dir, fps, dpi=dpi, debug=debug)

    # Add road
    scene.add_actor(Road())

    # NPC car
    npc = Car(pos=Point(30, 4),
              controller=Controller(Point(-10, 0)))
    npc.load_texture(heading="left")
    scene.add_actor(npc)

    # Ego vehicle
    egoController = PIDController(Point(20, 0), yref=0)
    scene.set_ego(Car(pos=Point(0, 0), controller=egoController))
    scene.ego.load_texture()
    scene.add_actor(scene.ego)

    # Real trajectory of ego vehicle
    real_meas = Trajectory(scene.ego, lambda x: x, scene.fps)
    real_meas.MARKER_SIZE = 10
    scene.add_actor(real_meas)

    # Real trajectory annotation
    real_meas_legend = TrajLegend(
        "Ground truth", Point(30, 5), start_time = 0.5, end_time=5,
        text_style={"color": real_meas.marker_style["color"]},
        marker_style=real_meas.marker_style)
    scene.add_actor(real_meas_legend)

    # GPS measurement of ego vehicle (add normal distribution errors)
    def gps_sampling(p: Point):
        return p + Point.nd_error(Point(0, 0), Point(.4, .4))
    gps_meas = Trajectory(scene.ego, gps_sampling, scene.fps, .1)
    gps_meas.marker_style["color"] = "green"
    gps_meas.line_style["color"] = "green"
    scene.add_actor(gps_meas)
    egoController.traj = gps_meas

    # GPS measurement annotation
    gps_meas_legend = TrajLegend(
        "Localization", Point(30, 3.5), start_time = 0.5, end_time=5,
        text_style={"color": gps_meas.marker_style["color"]},
        marker_style=gps_meas.marker_style)
    scene.add_actor(gps_meas_legend)

    scene.run(steps)
    scene.to_vid("benign.mp4")

def main():
    benign(debug=True)
    #  attack(debug=True)


if __name__ == "__main__":
    main()
