from Scene import Scene
from Point import Point
from Actor import *
from Controller import PIDController


def scene2(video_dir: str, debug: bool = False, high_quality: bool = False):
    fps = 60 if high_quality else 10
    dpi = 100

    ld_title_time = 1
    ld_explanation_time = ld_title_time + 1
    real_start_time = ld_explanation_time + 1
    msf_start_time = real_start_time + 3
    detect_start_time = msf_start_time + 1
    ar_box_time = detect_start_time + 2
    naive_ld2ar = ar_box_time + 3
    ld_attack_time = naive_ld2ar + 1
    fusion_time = ld_attack_time + 4
    suspicious_explanation_time = fusion_time + 8
    mux_time = suspicious_explanation_time + 5
    localization_time = mux_time + 2
    attack_time = localization_time + 3
    detected_time = attack_time + 2
    stop_time = detected_time + 5

    duration = stop_time + .5

    scene = Scene(video_dir, "scene2", duration, fps, dpi=dpi, debug=debug)

    ld_traj_color = "#40E0D0"
    gt_color = "grey"
    legend_color = "black"
    detect_color = "#87CEFA"
    loc_color = "#DDA0DD"
    sensor_direct_color = "black"
    attack_color = "red"

    # Add road
    road = Road()
    scene.add_actor(road)

    class ChangeSpeedCB(PeriodCB):
        actor: Car

        def __init__(self, speed_from: float, speed_to: float,
                     start_time: float = 0,
                     end_time: float = float("inf")) -> None:
            super().__init__(start_time, end_time)
            self.speed_from = speed_from
            self.speed_to = speed_to

        def step(self, time: float, view: Rect) -> None:
            super().step(time, view)
            self.actor.controller.speed.x = self.speed_from * \
                (1 - self.progress) + self.speed_to * self.progress

    # Ego vehicle
    egoSpeed = Point(15, 0)
    egoController = PIDController(egoSpeed, yref=0)
    ego = Car(pos=Point(0, 0), controller=egoController)
    ego.load_texture()
    ego.add_cb(ChangeSpeedCB(egoSpeed.x, 0, detected_time, stop_time))
    scene.set_ego(ego)
    scene.add_actor(ego)

    # Lane detection results
    ld_meas = LaneDetection(ego, road.get_lines(), Point(10, 0),
                            GetPos.gausian_meas(scale=Point(0, .1)),
                            sample_period=0.1)
    ld_meas.marker_style["color"] = ld_traj_color
    ld_meas.arrow_style["color"] = ld_meas.marker_style["color"]
    ld_meas.line_style["color"] = ld_meas.marker_style["color"]
    ld_meas.add_cb(FadeInOutCB(ld_explanation_time))
    scene.add_actor(ld_meas)

    def change_text_color(actor: Actor, color: str):
        actor.text_style["color"] = color

    # LD measurement annotation
    ld_meas_legend = TrajLegend(
        "LD", Point(1, 14), marker_style=ld_meas.marker_style)
    ld_meas_legend.marker_style['linewidth'] = 3
    ld_meas_legend.marker_style['color'] = ld_traj_color
    ld_meas_legend.add_cb(FadeInOutCB(ld_explanation_time))
    ld_meas_legend.add_cb(ChangeColorCB(
        ld_attack_time-1, 1, Color(ld_traj_color), Color("red"),
        change_text_color, False))
    ld_meas_legend.add_cb(ChangeColorCB(
        mux_time-1, 1, Color("red"), Color(ld_traj_color),
        change_text_color, False))
    scene.add_actor(ld_meas_legend)

    def use_ld_for_loc(actor: Car):
        actor.controller.meas = ld_meas
    ego.add_cb(ActionCB(use_ld_for_loc, detected_time))

    # Real trajectory of ego vehicle
    real_meas = Trajectory(ego)
    real_meas.MARKER_SIZE = 40
    real_meas.ANIMATION_TIME = -1
    real_meas.marker_style["marker"] = "o"
    real_meas.add_cb(FadeInOutCB(real_start_time, msf_start_time))
    scene.add_actor(real_meas)

    # Real trajectory annotation
    real_meas_legend = TrajLegend(
        "Ground truth", Point(1, 12.5), marker_style=real_meas.marker_style)
    real_meas_legend.marker_style['color'] = gt_color
    real_meas_legend.MARKER_SIZE = 120
    real_meas_legend.add_cb(FadeInOutCB(real_start_time, msf_start_time))
    scene.add_actor(real_meas_legend)

    def msf_attack_action(actor: Trajectory):
        class Attack:
            def __init__(self, yinit: int):
                self.y = yinit
                self.dy = 0.01
                self.time = 0

            def __call__(self, p: Point, time: float) -> Point:
                if time > attack_time:
                    self.y += self.dy
                    self.dy *= (1 + 0.1 * (time - self.time))
                else:
                    self.y = msf_meas.car.pos.y
                self.time = time
                return Point(p.x, self.y)

        actor._get_pos = Attack(0)

    def change_traj_color(actor: Actor, color: str):
        actor.marker_style["color"] = color
        actor.line_style["color"] = color

    # MSF measurement of ego vehicle (add normal distribution errors)
    msf_meas = Trajectory(ego, GetPos.gausian_meas(scale=Point(.2, .2)), .1)
    msf_meas.marker_style["color"] = "green"
    msf_meas.line_style["color"] = "green"
    msf_meas.add_cb(FadeInOutCB(msf_start_time))
    msf_meas.add_cb(ChangeColorCB(attack_time, 1.5, Color("green"),
                                  Color("red"), change_traj_color))
    msf_meas.add_cb(ActionCB(msf_attack_action, attack_time))
    scene.add_actor(msf_meas)
    egoController.meas = msf_meas

    # MSF measurement annotation
    msf_meas_legend = TrajLegend(
        "MSF", Point(1, 12.5), marker_style=msf_meas.marker_style)
    msf_meas_legend.marker_style['color'] = legend_color
    msf_meas_legend.add_cb(FadeInOutCB(msf_start_time))
    msf_meas_legend.add_cb(ChangeColorCB(
        attack_time, 1, Color(legend_color), Color("red"), change_text_color,
        False))
    scene.add_actor(msf_meas_legend)

    # Detect text box
    detect_text = Text("Attack detection", Point(8.8, 15), add_box=True)
    detect_text.text_style["size"] = 20
    detect_text.add_cb(FadeInOutCB(detect_start_time+1))
    scene.add_actor(detect_text)

    # Attack response text box
    attack_response_text_box = Text(
        "Attack response\n(e.g., safe in-lane stopping)",
        Point(16.3, 15), add_box=True)
    attack_response_text_box.text_style["size"] = 20
    attack_response_text_box.add_cb(FadeInOutCB(
        ar_box_time+1, mux_time, remove_after_fadeout=False))
    attack_response_text_box.add_cb(FadeInOutCB(detected_time))
    scene.add_actor(attack_response_text_box)

    # Fusion text box
    fusion_text_box = Text("Safety-driven fusion",
                           Point(7.6, 10), add_box=True)
    fusion_text_box.text_style["size"] = 20
    fusion_text_box.add_cb(FadeInOutCB(fusion_time+1))
    scene.add_actor(fusion_text_box)

    # detect_polyline
    ld2detect_poly = PolyLine(
        Point(4, 14.05), [Point(1.5, 0), Point(0, 1.15), Point(3, 0)], 1)
    ld2detect_poly.line_style["color"] = detect_color
    ld2detect_poly.add_cb(FadeInOutCB(detect_start_time))
    scene.add_actor(ld2detect_poly)

    def change_arrow_color(actor: Actor, color: str):
        actor.line_style["color"] = color
        actor.arrow_style["color"] = color

    msf2detect_poly = PolyLine(
        Point(4, 12.5), [Point(3.5, 0), Point(0, 2.3), Point(1, 0)], 1)
    msf2detect_poly.line_style["color"] = detect_color
    msf2detect_poly.add_cb(FadeInOutCB(detect_start_time))
    msf2detect_poly.add_cb(ChangeColorCB(
        attack_time, 1,
        Color(msf2detect_poly.line_style["color"]),
        Color(attack_color), change_arrow_color))
    scene.add_actor(msf2detect_poly)

    # Attack response poly lines
    detect2ar_poly = PolyLine(Point(13.4, 15), [Point(2.6, 0)], 1)
    detect2ar_poly.line_style["color"] = detect_color
    detect2ar_poly.add_cb(FadeInOutCB(
        ar_box_time, mux_time, remove_after_fadeout=False))
    detect2ar_poly.add_cb(FadeInOutCB(detected_time))
    scene.add_actor(detect2ar_poly)
    # Attack! text
    detect_attack_text = Text("Attack!", Point(13.5, 15.5))
    detect_attack_text.text_style["color"] = "red"
    detect_attack_text.text_style["size"] = 24
    detect_attack_text.add_cb(FadeInOutCB(ar_box_time+1, mux_time))
    scene.add_actor(detect_attack_text)
    # No attack text
    detect_no_attack_text = Text("No attack", Point(13.5, 15.5))
    detect_no_attack_text.text_style["color"] = "red"
    detect_no_attack_text.text_style["size"] = 22
    detect_no_attack_text.add_cb(FadeInOutCB(mux_time+1, attack_time))
    scene.add_actor(detect_no_attack_text)

    ld2ar_poly = PolyLine(Point(4, 13.95),
                          [Point(10, 0), Point(0, 1.05), Point(2, 0)], 1)
    ld2ar_poly.line_style["color"] = sensor_direct_color
    ld2ar_poly.add_cb(FadeInOutCB(naive_ld2ar, fusion_time))
    ld2ar_poly.add_cb(ChangeColorCB(
        ld_attack_time, 1, Color(sensor_direct_color), Color("red"),
        change_arrow_color, False))
    ld2ar_poly.add_cb(ChangeColorCB(
        fusion_time-1, 1, Color("red"), Color(sensor_direct_color),
        change_arrow_color, False))
    scene.add_actor(ld2ar_poly)

    loc2ar_poly = PolyLine(Point(18, 11.8), [Point(0, 2.4)], 1)
    loc2ar_poly.line_style["color"] = loc_color
    loc2ar_poly.add_cb(FadeInOutCB(detected_time))
    scene.add_actor(loc2ar_poly)

    # fusion_polyline
    ld2fusion_poly = PolyLine(
        Point(4, 14), [Point(2.5, 0), Point(0, -3.8), Point(.8, 0)], 1)
    ld2fusion_poly.line_style["color"] = loc_color
    ld2fusion_poly.add_cb(FadeInOutCB(fusion_time))
    ld2fusion_poly.add_cb(ChangeColorCB(
        fusion_time+1, 1, Color(loc_color), Color("red"),
        change_arrow_color, False))
    ld2fusion_poly.add_cb(ChangeColorCB(
        mux_time-1, 1, Color("red"), Color(loc_color),
        change_arrow_color, False))
    scene.add_actor(ld2fusion_poly)

    msf2fusion_poly = PolyLine(
        Point(4, 12.45), [Point(1.5, 0), Point(0, -2.65), Point(1.8, 0)], 1)
    msf2fusion_poly.line_style["color"] = loc_color
    msf2fusion_poly.add_cb(FadeInOutCB(fusion_time))
    msf2fusion_poly.add_cb(ChangeColorCB(
        attack_time, 1,
        Color(msf2fusion_poly.line_style["color"]),
        Color(attack_color), change_arrow_color))
    scene.add_actor(msf2fusion_poly)

    # Mux
    mux = Mux(Point(14, 11.275))
    mux.add_cb(FadeInOutCB(mux_time))
    scene.add_actor(mux)

    # Localization_text
    localization_text = Text("Localization", Point(16.3, 11.225), add_box=True)
    localization_text.text_style["size"] = 20
    localization_text.add_cb(FadeInOutCB(localization_time))
    scene.add_actor(localization_text)

    # mux_polyline
    msf2mux_poly = PolyLine(Point(4, 12.55), [Point(10, 0)], 1)
    msf2mux_poly.line_style["color"] = sensor_direct_color
    msf2mux_poly.add_cb(FadeInOutCB(mux_time))
    msf2mux_poly.add_cb(ChangeColorCB(
        attack_time, 1,
        Color(msf2mux_poly.line_style["color"]),
        Color(attack_color), change_arrow_color))
    scene.add_actor(msf2mux_poly)

    fusion2mux_poly = PolyLine(Point(13.1, 10), [Point(.9, 0)], 1)
    fusion2mux_poly.line_style["color"] = loc_color
    fusion2mux_poly.add_cb(FadeInOutCB(mux_time))
    scene.add_actor(fusion2mux_poly)

    detect2mux_poly = PolyLine(Point(13.4, 15), [Point(1.1, 0), Point(0, -2.2)], 1)
    detect2mux_poly.line_style["color"] = detect_color
    detect2mux_poly.add_cb(FadeInOutCB(mux_time+1))
    scene.add_actor(detect2mux_poly)

    mux2localization_poly = PolyLine(Point(15, 11.225), [Point(1, 0)], 1)
    mux2localization_poly.line_style["color"] = sensor_direct_color
    mux2localization_poly.add_cb(FadeInOutCB(localization_time))
    mux2localization_poly.add_cb(ChangeColorCB(
        detected_time, 1,
        Color(mux2localization_poly.line_style["color"]),
        Color(loc_color), change_arrow_color))
    scene.add_actor(mux2localization_poly)

    # Attacker image
    # TODO: switch control to ld, and add attack to ld. Change ld color to red
    ld_attacker = Image("pics/attacker.png", Point(1.5, 15.2), w=1.5, h=1.5)
    ld_attacker.texture.image_style["zorder"] = 99
    ld_attacker.add_cb(ImageGrowCB(ld_attack_time-.2, ld_attack_time))
    ld_attacker.add_cb(FadeInOutCB(ld_attack_time-.2, mux_time))
    scene.add_actor(ld_attacker)

    gps_attacker = Image("pics/attacker.png", Point(2.5, 9), w=3, h=3)
    gps_attacker.texture.image_style["zorder"] = 99
    gps_attacker.add_cb(ImageGrowCB(attack_time-.2, attack_time))
    scene.add_actor(gps_attacker)

    # Signal image
    spoofing_signal = Image(
        "pics/signal.png", Point(4.5, 7), w=4, h=4, rotate_degree=215)
    spoofing_signal.texture.image_style["zorder"] = 99
    spoofing_signal.add_cb(
        ImageGrowCB(attack_time, attack_time+.2))
    scene.add_actor(spoofing_signal)

    # Detected text
    detected_text = Text("Attack detected!", Point(8, 16))
    detected_text.text_style["color"] = "red"
    detected_text.text_style["size"] = 26
    detected_text.add_cb(FadeInOutCB(detected_time-1))
    scene.add_actor(detected_text)

    # Use fusion text
    use_fusion_text = Text("Use safety-driven fusion results", Point(16, 10))
    use_fusion_text.text_style["color"] = "red"
    use_fusion_text.text_style["size"] = 18
    use_fusion_text.add_cb(FadeInOutCB(detected_time))
    scene.add_actor(use_fusion_text)

    # Slowing down text
    stopping_text = Text("Try to have safe in-lane stopping", Point(16, 16.5))
    stopping_text.text_style["color"] = "red"
    stopping_text.text_style["size"] = 18
    stopping_text.add_cb(FadeInOutCB(detected_time))
    scene.add_actor(stopping_text)

    titles = TextList([
        ("Lane detection (LD)", ld_title_time, msf_start_time),
        (["$L$", "$D$", "${ }^3$"] +
         list(": A Novel LD based defense"), msf_start_time, float('inf')),
    ], Point(1, scene.camera.limits.y-.5))
    for title in titles.actors:
        title.text_style["size"] = 48
        title.text_style["verticalalignment"] = "baseline"
    scene.add_actor(titles)

    explanations = TextList([
        ("\nLD can be used for local localization, and the vehicle knows its position within the lane.",
         ld_explanation_time, msf_start_time),
        ("The first to use a local localization method (LD) to defend against attacks on\n"
         "global localization. LD3 first cross-check with MSF to detect attacks,\n"
         "and then perform safe in-lane stopping to best avoid accidents.",
         msf_start_time, naive_ld2ar),
        ("For localization, we can naively fully trust LD, but that is vulnerable to LD attacks.",
         naive_ld2ar, fusion_time),
        ("Instead, we design a novel safety-driven fusion to fuse MSF and LD based on their\n"
         "aggressiveness to cause lane departure.",
         fusion_time, suspicious_explanation_time),
        ("This way, no matter the attacker chooses to attack LD or MSF,\n"
         "the attack effect will be penalized in the fusion process\n"
         "to best achieve safe in-lane stopping.",
         suspicious_explanation_time, mux_time),
        ("Without attack, results from MSF is used as localization.",
         mux_time, attack_time),
        ("With attack, fusion results are used for localization to slow down within the lane.",
         attack_time, float("inf")),
    ], Point(1, scene.camera.limits.y-1.5), typing_effect=False)
    for explanation in explanations.actors:
        explanation.text_style["size"] = 24
    scene.add_actor(explanations)

    #  scene.run(start_time=mux_time, end_time=mux_time + 4)
    scene.run(ending_freeze_time=1)
    scene.to_vid()
