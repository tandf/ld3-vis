#! /bin/env python3

from __future__ import annotations
import os

from Scene import Scene
from Point import Point
from Actor import *
from Controller import *


dir_path = os.path.dirname(os.path.realpath(__file__))
video_dir = os.path.join(dir_path, "videos")

if not os.path.isdir(video_dir):
    os.mkdir(video_dir)


def scene1(debug: bool = False, high_quality: bool = False):
    duration = 18  # seconds
    fps = 60 if high_quality else 10
    dpi = 100

    scene = Scene(video_dir, "scene1", duration, fps, dpi=dpi, debug=debug)

    # Add road
    road = Road()
    scene.add_actor(road)

    # NPCs
    npc1 = Car(pos=Point(25, 4),
              controller=Controller(Point(10, 0)))
    npc1.load_texture(heading="right")
    scene.add_actor(npc1)
    npc2 = Car(pos=Point(129.3, 4),
              controller=Controller(Point(8, 0)))
    npc2.load_texture(heading="right")
    scene.add_actor(npc2)

    # Ego vehicle
    egoController = PIDController(Point(15, 0), yref=0)
    scene.set_ego(Car(pos=Point(0, 0), controller=egoController))
    scene.ego.load_texture()
    scene.add_actor(scene.ego)

    gps_start_time = 1
    # GPS measurement of ego vehicle (add normal distribution errors)
    gps_meas = Trajectory(
        scene.ego, GetPos.gausian_meas(scale=Point(.4, .4)), .15)
    gps_meas.marker_style["color"] = "#000080"
    gps_meas.line_style["color"] = "#000080"
    gps_meas.add_cb(FadeInOutCB(gps_start_time, gps_start_time+2.5))
    scene.add_actor(gps_meas)
    egoController.traj = gps_meas

    lidar_start_time = 2.5
    # LiDAR measurement of ego vehicle (add normal distribution errors)
    lidar_meas = Trajectory(
        scene.ego, GetPos.gausian_meas(scale=Point(.4, .4)), .25)
    lidar_meas.marker_style["color"] = "#EE82EE"
    lidar_meas.line_style["color"] = "#EE82EE"
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

    gps_attack_start_time = 11
    # GPS measurement annotation
    gps_meas_legend = TrajLegend(
        "GPS", Point(2, 13), marker_style=gps_meas.marker_style)
    gps_meas_legend.add_cb(FadeInOutCB(gps_start_time, gps_attack_start_time))
    scene.add_actor(gps_meas_legend)

    gps_attack_meas_legend = TrajLegend(
        "GPS", Point(2, 13), marker_style=gps_meas.marker_style)
    gps_attack_meas_legend.text_style["color"] = "red"
    gps_attack_meas_legend.add_cb(FadeInOutCB(gps_attack_start_time))
    scene.add_actor(gps_attack_meas_legend)

    # LiDAR measurement annotation
    lidar_meas_legend = TrajLegend(
        "LiDAR", Point(2, 12), marker_style=lidar_meas.marker_style)
    lidar_meas_legend.add_cb(FadeInOutCB(lidar_start_time))
    scene.add_actor(lidar_meas_legend)

    # IMU measurement annotation
    imu_meas_legend = TrajLegend(
        "IMU", Point(2, 11), marker_style=imu_meas.marker_style)
    imu_meas_legend.add_cb(FadeInOutCB(imu_start_time))
    scene.add_actor(imu_meas_legend)

    msf_start_time = 6
    gps_attack_effect_time = gps_attack_start_time + 2
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
        "MSF", Point(9, 12), marker_style=msf_meas.marker_style)
    msf_meas_legend.add_cb(FadeInOutCB(msf_start_time, gps_attack_effect_time))
    scene.add_actor(msf_meas_legend)

    # Attacker measurement
    class Attack:
        def __init__(self, yinit: int):
            self.y = yinit
            self.dy = -0.04
            self.time = 0
        def __call__(self, p: Point, time: float) -> Point:
            if time > gps_attack_effect_time:
                self.y += self.dy
                self.dy *= (1 + 0.04 * (time - self.time))
            else:
                self.y = msf_meas.car.pos.y
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
        "MSF", Point(9, 12), marker_style=msf_meas.marker_style)
    attack_meas_legend.text_style["color"] = "red"
    attack_meas_legend.marker_style["color"] = "red"
    attack_meas_legend.add_cb(FadeInOutCB(gps_attack_effect_time))
    scene.add_actor(attack_meas_legend)

    # Polylines
    gps_poly = PolyLine(
        Point(6, 13), [Point(1, 0), Point(0, -1), Point(1, 0)], 1)
    gps_poly.add_cb(FadeInOutCB(msf_start_time, gps_attack_start_time))
    scene.add_actor(gps_poly)

    gps_attack_poly = PolyLine(
        Point(6, 13), [Point(1, 0), Point(0, -1), Point(1, 0)], 1)
    gps_attack_poly.line_style["color"] = "red"
    gps_attack_poly.line_style["zorder"] = 10
    gps_attack_poly.add_cb(FadeInOutCB(gps_attack_start_time+1))
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
    real_meas.MARKER_SIZE = 40
    real_meas.ANIMATION_TIME = -1
    real_meas.marker_style["marker"] = "o"
    real_meas.add_cb(FadeInOutCB(real_start_time))
    scene.add_actor(real_meas)

    # Real trajectory annotation
    real_meas_legend = TrajLegend(
        "Ground truth", Point(9, 13), marker_style=real_meas.marker_style)
    real_meas_legend.MARKER_SIZE = 120
    real_meas_legend.add_cb(FadeInOutCB(real_start_time))
    scene.add_actor(real_meas_legend)

    # Attacker image
    attacker = Image("pics/attacker.png", Point(23, 13), w=3, h=3)
    attacker.texture.image_style["zorder"] = 99
    attacker.add_cb(ImageGrow(gps_attack_start_time-.2, gps_attack_start_time))
    scene.add_actor(attacker)

    # Signal image
    spoofing_signal = Image(
        "pics/signal.png", Point(20.5, 10.5), w=4, h=4, rotate_degree=135)
    spoofing_signal.texture.image_style["zorder"] = 99
    spoofing_signal.add_cb(
        ImageGrow(gps_attack_start_time, gps_attack_start_time+.2))
    scene.add_actor(spoofing_signal)

    # GPS Spoofing text
    gps_spoofing_text = Text("GPS spoofing", Point(22, 10.5))
    gps_spoofing_text.text_style["color"] = "red"
    gps_spoofing_text.add_cb(FadeInOutCB(gps_attack_start_time))
    scene.add_actor(gps_spoofing_text)

    # Crash image
    crash = Image("pics/crash.png", Point(17, 7), 4, 4)
    crash.texture.image_style["zorder"] = 99
    crash.add_cb(ImageGrow(17.8, 18))
    scene.add_actor(crash)

    #  ld_start_time = 10
    #  # Lane detection results
    #  ld_meas = LaneDetection(scene.ego, road.get_lines(), Point(10, 0),
                            #  GetPos.gausian_meas(scale=Point(0, .2)))
    #  ld_meas.add_cb(FadeInOutCB(ld_start_time))
    #  scene.add_actor(ld_meas)

    #  # LD measurement annotation
    #  ld_meas_legend = TrajLegend(
        #  "LD", Point(9, 11), marker_style=ld_meas.marker_style)
    #  ld_meas_legend.add_cb(FadeInOutCB(ld_start_time))
    #  scene.add_actor(ld_meas_legend)

    titles = TextList([
        ("Multi-Sensor Fusion (MSF)", 0, gps_attack_start_time-1),
        ("FusionRipper attack", gps_attack_start_time-1, float("inf")),
        ], Point(1, scene.camera.limits.y))
    for title in titles.actors:
        title.text_style["size"] = 48
    scene.add_actor(titles)

    explanations = TextList([
        ("MSF fuses inputs from different sensors to get the vehicle localization.",
         1, gps_attack_start_time),
        ("FusionRipper attack can attack MSF results by spoofing only GPS signal.",
         gps_attack_start_time, float("inf")),
    ], Point(1, scene.camera.limits.y-2), typing_effect=False)
    for explanation in explanations.actors:
        explanation.text_style["size"] = 24
    scene.add_actor(explanations)

    scene.run(ending_freeze_time=2)
    scene.to_vid()

def main():
    debug = False
    high_quality = True
    scene1(debug=debug, high_quality=high_quality)


if __name__ == "__main__":
    main()
