#! /bin/env python3

from __future__ import annotations
import os

from Scene import Scene
from Point import Point
from Actor import *
from Controller import *


dir_path = os.path.dirname(os.path.realpath(__file__))


def scene1(debug: bool = False):
    duration = 15  # second

    fps = 10 if debug else 60
    dpi = 100
    steps = fps * duration

    scene = Scene(dir_path, "scene1", fps, dpi=dpi, debug=debug)

    # Add road
    road = Road()
    scene.add_actor(road)

    # NPC car
    npc = Car(pos=Point(25, 4),
              controller=Controller(Point(-10, 0)))
    npc.load_texture(heading="left")
    scene.add_actor(npc)

    # Ego vehicle
    egoController = PIDController(Point(15, 0), yref=0)
    scene.set_ego(Car(pos=Point(0, 0), controller=egoController))
    scene.ego.load_texture()
    scene.add_actor(scene.ego)

    gps_start_time = 1
    # GPS measurement of ego vehicle (add normal distribution errors)
    gps_meas = Trajectory(
        scene.ego, GetPos.gausian_meas(scale=Point(.4, .4)), .15)
    gps_meas.marker_style["color"] = "#D2691E"
    gps_meas.line_style["color"] = "#D2691E"
    gps_meas.add_cb(FadeInOutCB(gps_start_time, gps_start_time+2.5))
    scene.add_actor(gps_meas)
    egoController.traj = gps_meas

    lidar_start_time = 2.5
    # LiDAR measurement of ego vehicle (add normal distribution errors)
    lidar_meas = Trajectory(
        scene.ego, GetPos.gausian_meas(scale=Point(.4, .4)), .25)
    lidar_meas.marker_style["color"] = "#6A5ACD"
    lidar_meas.line_style["color"] = "#6A5ACD"
    lidar_meas.add_cb(FadeInOutCB(lidar_start_time, lidar_start_time+2.5))
    scene.add_actor(lidar_meas)
    egoController.traj = lidar_meas

    imu_start_time = 4
    # IMU measurement of ego vehicle (add normal distribution errors)
    imu_meas = Trajectory(
        scene.ego, GetPos.gausian_meas(scale=Point(.4, .4)), .1)
    imu_meas.marker_style["color"] = "#5F9EA0"
    imu_meas.line_style["color"] = "#5F9EA0"
    imu_meas.add_cb(FadeInOutCB(imu_start_time, imu_start_time+2.5))
    scene.add_actor(imu_meas)
    egoController.traj = imu_meas

    gps_attack_start_time = 10
    # GPS measurement annotation
    gps_meas_legend = TrajLegend(
        "GPS", Point(2, 13),
        text_style={"color": gps_meas.marker_style["color"]},
        marker_style=gps_meas.marker_style)
    gps_meas_legend.add_cb(FadeInOutCB(gps_start_time, gps_attack_start_time))
    scene.add_actor(gps_meas_legend)

    gps_attack_meas_legend = TrajLegend(
        "GPS", Point(2, 13),
        text_style={"color": "red"},
        marker_style=gps_meas.marker_style)
    gps_attack_meas_legend.marker_style["color"] = "red"
    gps_attack_meas_legend.add_cb(FadeInOutCB(gps_attack_start_time))
    scene.add_actor(gps_attack_meas_legend)

    # LiDAR measurement annotation
    lidar_meas_legend = TrajLegend(
        "LiDAR", Point(2, 12),
        text_style={"color": lidar_meas.marker_style["color"]},
        marker_style=lidar_meas.marker_style)
    lidar_meas_legend.add_cb(FadeInOutCB(lidar_start_time))
    scene.add_actor(lidar_meas_legend)

    # IMU measurement annotation
    imu_meas_legend = TrajLegend(
        "IMU", Point(2, 11),
        text_style={"color": imu_meas.marker_style["color"]},
        marker_style=imu_meas.marker_style)
    imu_meas_legend.add_cb(FadeInOutCB(imu_start_time))
    scene.add_actor(imu_meas_legend)

    msf_start_time = 6
    gps_attack_effect_time = gps_attack_start_time + 1
    # MSF measurement of ego vehicle (add normal distribution errors)
    msf_meas = Trajectory(
        scene.ego, GetPos.gausian_meas(scale=Point(.1, .1)), .1)
    msf_meas.marker_style["color"] = "green"
    msf_meas.line_style["color"] = "green"
    msf_meas.add_cb(FadeInOutCB(msf_start_time))
    msf_meas.add_cb(TrajAddPosLifecycleCB(end_time=gps_attack_effect_time))
    scene.add_actor(msf_meas)
    egoController.traj = msf_meas

    # MSF measurement annotation
    msf_meas_legend = TrajLegend(
        "MSF", Point(9, 12),
        text_style={"color": msf_meas.marker_style["color"]},
        marker_style=msf_meas.marker_style)
    msf_meas_legend.add_cb(FadeInOutCB(msf_start_time, gps_attack_effect_time))
    scene.add_actor(msf_meas_legend)

    # Attacker measurement
    class Attack:
        def __init__(self, yinit: int):
            self.y = yinit
            self.dy = -0.1
            self.time = 0
        def __call__(self, p: Point, time: float) -> Point:
            if time > gps_attack_effect_time:
                self.y += self.dy
                self.dy *= (1 + 0.03 * (time - self.time))
            self.time = time
            return Point(p.x, self.y)

    # Attacker measurement
    msf_attack_meas = Trajectory(scene.ego, Attack(0), .1)
    msf_attack_meas.marker_style["color"] = "red"
    msf_attack_meas.line_style["color"] = "red"
    msf_attack_meas.add_cb(FadeInOutCB(gps_attack_effect_time))
    msf_attack_meas.add_cb(TrajAddPosLifecycleCB(gps_attack_effect_time))
    scene.add_actor(msf_attack_meas)
    egoController.traj = msf_attack_meas

    # MSF measurement annotation
    attack_meas_legend = TrajLegend(
        "MSF", Point(9, 12),
        text_style={"color": "red"},
        marker_style=msf_meas.marker_style)
    attack_meas_legend.marker_style["color"] = "red"
    attack_meas_legend.add_cb(FadeInOutCB(gps_attack_effect_time))
    scene.add_actor(attack_meas_legend)

    # Polylines
    gps_poly = PolyLine(Point(6, 13), [Point(
        1, 0), Point(0, -1), Point(1, 0)], 1)
    gps_poly.add_cb(FadeInOutCB(msf_start_time, gps_attack_start_time))
    scene.add_actor(gps_poly)

    gps_attack_poly = PolyLine(
        Point(6, 13), [Point(1, 0), Point(0, -1), Point(1, 0)], 0)
    gps_attack_poly.line_style["color"] = "red"
    gps_attack_poly.line_style["zorder"] = 10
    gps_attack_poly.add_cb(FadeInOutCB(gps_attack_effect_time))
    scene.add_actor(gps_attack_poly)

    lidar_poly = PolyLine(Point(6, 12), [Point(2, 0)], 1)
    lidar_poly.add_cb(FadeInOutCB(msf_start_time))
    scene.add_actor(lidar_poly)

    imu_poly = PolyLine(
        Point(6, 11), [Point(1, 0), Point(0, 1), Point(1, 0)], 1)
    imu_poly.add_cb(FadeInOutCB(msf_start_time))
    scene.add_actor(imu_poly)

    real_start_time = 7
    # Real trajectory of ego vehicle
    real_meas = Trajectory(scene.ego)
    real_meas.MARKER_SIZE = 20
    real_meas.ANIMATION_TIME = -1
    real_meas.marker_style["marker"] = "o"
    real_meas.add_cb(FadeInOutCB(real_start_time))
    scene.add_actor(real_meas)

    # Real trajectory annotation
    real_meas_legend = TrajLegend(
        "Ground truth", Point(9, 13),
        text_style={"color": real_meas.marker_style["color"]},
        marker_style=real_meas.marker_style)
    real_meas_legend.MARKER_SIZE = 60
    real_meas_legend.add_cb(FadeInOutCB(real_start_time))
    scene.add_actor(real_meas_legend)

    ld_start_time = 10
    # Lane detection results
    ld_meas = LaneDetection(scene.ego, road.get_lines(), Point(10, 0),
                            GetPos.gausian_meas(scale=Point(0, .2)))
    ld_meas.add_cb(FadeInOutCB(ld_start_time))
    scene.add_actor(ld_meas)

    # LD measurement annotation
    ld_meas_legend = TrajLegend(
        "LD", Point(9, 11),
        text_style={"color": ld_meas.marker_style["color"]},
        marker_style=ld_meas.marker_style)
    ld_meas_legend.add_cb(FadeInOutCB(ld_start_time))
    scene.add_actor(ld_meas_legend)

    scene.run(steps)
    scene.to_vid()

def main():
    scene1(debug=False)


if __name__ == "__main__":
    main()
