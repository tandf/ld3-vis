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
    steps = 50 if debug else 500

    scene = Scene(dir_path, "attack", fps, dpi=dpi, debug=debug)

    # Add road
    scene.add_actor(Road())

    # NPC car
    npc = Car(pos=Point(25, 4),
              controller=Controller(Point(-10, 0)))
    npc.load_texture(heading="left")
    scene.add_actor(npc)

    # Ego vehicle
    egoController = PIDController(Point(20, 0), yref=0)
    scene.set_ego(Car(pos=Point(0, 0), controller=egoController))
    scene.ego.load_texture()
    scene.add_actor(scene.ego)

    # Real trajectory of ego vehicle
    real_meas = Trajectory(scene.ego, lambda x, t: x, scene.fps)
    real_meas.MARKER_SIZE = 10
    real_meas.add_cb(FadeInOutCB(start_time=0.5))
    scene.add_actor(real_meas)

    # Real trajectory annotation
    real_meas_legend = TrajLegend(
        "Ground truth", Point(25, 5),
        text_style={"color": real_meas.marker_style["color"]},
        marker_style=real_meas.marker_style)
    real_meas_legend.add_cb(FadeInOutCB(start_time=0.5, end_time=5))
    scene.add_actor(real_meas_legend)

    # Attacker measurement
    class Attack:
        def __init__(self, yinit: int):
            self.y = yinit
            self.dy = -0.1
            self.time = 0
        def __call__(self, p: Point, time: float) -> Point:
            if time > 2:
                self.y += self.dy
                self.dy *= (1 + 0.03 * (time - self.time))
            self.time = time
            return Point(p.x, self.y)
    msf_meas = Trajectory(scene.ego, Attack(0), scene.fps, .1)
    msf_meas.marker_style["color"] = "green"
    msf_meas.line_style["color"] = "green"
    msf_meas.add_cb(FadeInOutCB(start_time=0.5))
    msf_meas.add_cb(TrajAddPosLifecycleCB(end_time=2))
    scene.add_actor(msf_meas)
    egoController.traj = msf_meas

    # MSF measurement annotation
    msf_meas_legend = TrajLegend(
        "MSF", Point(25, 3.5),
        text_style={"color": msf_meas.marker_style["color"]},
        marker_style=msf_meas.marker_style)
    msf_meas_legend.add_cb(FadeInOutCB(start_time=0.5, end_time=2))
    scene.add_actor(msf_meas_legend)

    # Attacker measurement
    attack_meas = Trajectory(scene.ego, Attack(0), scene.fps, .1)
    attack_meas.marker_style["color"] = "red"
    attack_meas.line_style["color"] = "red"
    attack_meas.add_cb(FadeInOutCB(start_time=0.5))
    attack_meas.add_cb(TrajAddPosLifecycleCB(start_time=2))
    scene.add_actor(attack_meas)
    egoController.traj = attack_meas

    # MSF measurement (attacked) annotation
    attack_meas_legend = TrajLegend(
        "MSF (attacked)", Point(25, 3.5),
        text_style={"color": attack_meas.marker_style["color"]},
        marker_style=attack_meas.marker_style)
    attack_meas_legend.add_cb(FadeInOutCB(start_time=2, end_time=5))
    scene.add_actor(attack_meas_legend)

    scene.run(steps)
    scene.to_vid()

def benign(debug:bool=False):
    fps = 10 if debug else 60
    dpi = 100
    steps = 50 if debug else 500

    scene = Scene(dir_path, "benign", fps, dpi=dpi, debug=debug)

    # Add road
    scene.add_actor(Road())

    # NPC car
    npc = Car(pos=Point(25, 4),
              controller=Controller(Point(-10, 0)))
    npc.load_texture(heading="left")
    scene.add_actor(npc)

    # Ego vehicle
    egoController = PIDController(Point(20, 0), yref=0)
    scene.set_ego(Car(pos=Point(0, 0), controller=egoController))
    scene.ego.load_texture()
    scene.add_actor(scene.ego)

    # Real trajectory of ego vehicle
    real_meas = Trajectory(scene.ego, lambda x, t: x, scene.fps)
    real_meas.MARKER_SIZE = 10
    real_meas.add_cb(FadeInOutCB(start_time=0.5))
    scene.add_actor(real_meas)

    # Real trajectory annotation
    real_meas_legend = TrajLegend(
        "Ground truth", Point(25, 5),
        text_style={"color": real_meas.marker_style["color"]},
        marker_style=real_meas.marker_style)
    real_meas_legend.add_cb(FadeInOutCB(start_time=0.5, end_time=5))
    scene.add_actor(real_meas_legend)

    # MSF measurement of ego vehicle (add normal distribution errors)
    def msf_sampling(p: Point, time: float):
        return p + Point.nd_error(Point(0, 0), Point(.4, .4))
    msf_meas = Trajectory(scene.ego, msf_sampling, scene.fps, .1)
    msf_meas.marker_style["color"] = "green"
    msf_meas.line_style["color"] = "green"
    msf_meas.add_cb(FadeInOutCB(start_time=1.5))
    scene.add_actor(msf_meas)
    egoController.traj = msf_meas

    # MSF measurement annotation
    msf_meas_legend = TrajLegend(
        "MSF", Point(25, 3.5),
        text_style={"color": msf_meas.marker_style["color"]},
        marker_style=msf_meas.marker_style)
    msf_meas_legend.add_cb(FadeInOutCB(start_time=1.5, end_time=5))
    scene.add_actor(msf_meas_legend)

    scene.run(steps)
    scene.to_vid()

def main():
    #  benign(debug=True)
    attack(debug=True)


if __name__ == "__main__":
    main()
