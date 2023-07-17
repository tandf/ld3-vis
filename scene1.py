from Scene import Scene
from Point import Point
from Actor import *
from Controller import *


def scene1(video_dir: str, debug: bool = False, high_quality: bool = False,
           dpi: int = 100):
    fps = 60 if high_quality else 10

    gps_start_time = 3
    lidar_start_time = gps_start_time + 4
    imu_start_time = lidar_start_time + 4
    msf_start_time = imu_start_time + 4
    gps_attack_start_time = msf_start_time + 4
    crash_time = gps_attack_start_time + 4
    duration = crash_time # seconds

    scene = Scene(video_dir, "scene1", duration, fps, dpi=dpi, debug=debug)

    # Add road
    road = Road()
    scene.add_actor(road)

    # NPCs
    npc1 = Car(pos=Point(25, 4),
              controller=Controller(Point(10, 0)))
    npc1.load_texture(heading="right")
    scene.add_actor(npc1)
    npc2 = Car(pos=Point(164, 4),
              controller=Controller(Point(8, 0)))
    npc2.load_texture(heading="right")
    scene.add_actor(npc2)

    # Ego vehicle
    egoController = PIDController(Point(15, 0), yref=0, pid=(1, .2, 0))
    scene.set_ego(Car(pos=Point(0, 0), controller=egoController))
    scene.ego.load_texture()
    scene.add_actor(scene.ego)

    # GPS measurement of ego vehicle (add normal distribution errors)
    gps_meas = Trajectory(
        scene.ego, GetPos.gausian_meas(scale=Point(.4, .4)), .15)
    gps_meas.marker_style["color"] = "#000080"
    gps_meas.line_style["color"] = "#000080"
    gps_meas.add_cb(FadeInOutCB(gps_start_time, gps_start_time+2.5))
    scene.add_actor(gps_meas)
    egoController.meas = gps_meas

    # LiDAR measurement of ego vehicle (add normal distribution errors)
    lidar_meas = Trajectory(
        scene.ego, GetPos.gausian_meas(scale=Point(.4, .4)), .25)
    lidar_meas.marker_style["color"] = "#EE82EE"
    lidar_meas.line_style["color"] = "#EE82EE"
    lidar_meas.add_cb(FadeInOutCB(lidar_start_time, lidar_start_time+2.5))
    scene.add_actor(lidar_meas)
    egoController.meas = lidar_meas

    # IMU measurement of ego vehicle (add normal distribution errors)
    imu_meas = Trajectory(
        scene.ego, GetPos.gausian_meas(scale=Point(.4, .4)), .1)
    imu_meas.marker_style["color"] = "#5F9EA0"
    imu_meas.line_style["color"] = "#5F9EA0"
    imu_meas.add_cb(FadeInOutCB(imu_start_time, imu_start_time+2.5))
    scene.add_actor(imu_meas)
    egoController.meas = imu_meas

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

    gps_attack_effect_time = gps_attack_start_time + 1
    # MSF measurement of ego vehicle (add normal distribution errors)
    msf_meas = Trajectory(
        scene.ego, GetPos.gausian_meas(scale=Point(.1, .1)), .1)
    msf_meas.marker_style["color"] = "green"
    msf_meas.line_style["color"] = "green"
    msf_meas.add_cb(FadeInOutCB(msf_start_time))
    msf_meas.add_cb(TrajAddPosLifecycleCB(end_time=gps_attack_effect_time))
    scene.add_actor(msf_meas)
    egoController.meas = msf_meas

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
    egoController.meas = msf_attack_meas

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
    gps_attack_poly.line_style["zorder"] = 99
    gps_attack_poly.add_cb(FadeInOutCB(gps_attack_start_time+.5))
    scene.add_actor(gps_attack_poly)

    lidar_poly = PolyLine(Point(6, 12), [Point(2, 0)], 1)
    lidar_poly.add_cb(FadeInOutCB(msf_start_time))
    scene.add_actor(lidar_poly)

    imu_poly = PolyLine(
        Point(6, 11), [Point(1, 0), Point(0, 1), Point(1, 0)], 1)
    imu_poly.add_cb(FadeInOutCB(msf_start_time))
    scene.add_actor(imu_poly)

    # Attacker image
    attacker = Image("pics/attacker.png", Point(2.5, 9), w=3, h=3)
    attacker.texture.image_style["zorder"] = 99
    attacker.add_cb(ImageGrowCB(gps_attack_start_time-.2, gps_attack_start_time))
    scene.add_actor(attacker)

    # Signal image
    spoofing_signal = Image(
        "pics/signal.png", Point(4.8, 7.2), w=4, h=4, rotate_degree=230)
    spoofing_signal.texture.image_style["zorder"] = 99
    spoofing_signal.add_cb(
        ImageGrowCB(gps_attack_start_time, gps_attack_start_time+.2))
    scene.add_actor(spoofing_signal)

    # GPS Spoofing text
    gps_spoofing_text = Text("GPS spoofing", Point(4.5, 9.5))
    gps_spoofing_text.text_style["color"] = "red"
    gps_spoofing_text.add_cb(FadeInOutCB(gps_attack_start_time))
    scene.add_actor(gps_spoofing_text)

    # Crash image
    crash = Image("pics/crash.png", Point(17, 6.5), 4, 4)
    crash.texture.image_style["zorder"] = 99
    crash.add_cb(ImageGrowCB(crash_time-.2, crash_time))
    scene.add_actor(crash)

    titles = TextList([
        ("Multi-Sensor Fusion (MSF)", 0, gps_attack_start_time-1),
        (list("FusionRipper") + ["$^{[1]}$"] + list(" attack"),
         gps_attack_start_time-1, float("inf")),
    ], Point(1, scene.camera.limits.y-.5))
    for title in titles.actors:
        title.text_style["size"] = 48
        title.text_style["verticalalignment"] = "baseline"
    scene.add_actor(titles)

    explanations = TextList([
        ("MSF fuses inputs from different sensors to get the vehicle localization.",
         .5, gps_attack_start_time-1),
        ("FusionRipper attack can attack MSF results by spoofing only GPS signal.",
         gps_attack_start_time, float("inf")),
    ], Point(1, scene.camera.limits.y-1.5), typing_effect=False)
    for explanation in explanations.actors:
        explanation.text_style["size"] = 22
    scene.add_actor(explanations)

    # Citation text: Cite the FusionRipper paper
    citatoin_text = """[1] J. Shen, J. Y. Won, Z. Chen, and Q. A. Chen, “Drift with Devil: Security of Multi-Sensor Fusion based
     Localization in High-Level Autonomous Driving under GPS Spoofing,” in USENIX Security, 2020."""
    citation = Text(citatoin_text, Point(.5, .1))
    citation.text_style["size"] = 22
    citation.add_cb(FadeInOutCB(gps_attack_start_time-1))
    scene.add_actor(citation)

    scene.run(ending_freeze_time=2)
    # scene.run(start_time=crash_time-2, ending_freeze_time=2)
    scene.to_vid()