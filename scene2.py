from Scene import Scene
from Point import Point
from Actor import *
from Controller import PIDController


def scene2(video_dir: str, debug: bool = False, high_quality: bool = False):
    fps = 60 if high_quality else 10
    dpi = 100

    ld_title_time = .5
    real_start_time = ld_title_time + 1
    msf_start_time = real_start_time + 3
    detect_start_time = msf_start_time + 1
    ar_box_time = detect_start_time + 1
    naive_ld2ar = ar_box_time + 4
    ld_attack_time = naive_ld2ar + 3
    fusion_time = ld_attack_time + 4
    fusion2ar_time = fusion_time + 2
    suspicious_explanation_time = fusion2ar_time + 4
    mux_time = suspicious_explanation_time + 4
    localization_time = mux_time + 2
    attack_time = localization_time + 4
    detected_time = attack_time + 2
    stop_time = detected_time + 4

    duration = stop_time + .5

    scene = Scene(video_dir, "scene2", duration, fps, dpi=dpi, debug=debug)

    # Colors
    ld_traj_color = "#40E0D0"
    gt_color = "grey"
    legend_color = "black"
    detect_color = "#87CEFA"
    loc_color = "#DDA0DD"
    sensor_direct_color = "black"
    attack_color = "red"

    # Font size
    box_text_size = 16

    # Positions
    legend_right = 3.5
    detect_right = 11
    fusion_right = 10.6
    mux_left = 11.6
    mux_right = mux_left + 1
    ar_left = 13.8
    loc_left = ar_left + 1.8

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

    normal_ld_meas = GetPos.gausian_meas(scale=Point(0, .1))
    attack_ld_meas = GetPos.gausian_meas(loc=Point(0, 2), scale=Point(0, .1))
    def ld_meas_attack_action(actor: LaneDetection):
        actor._get_pos = attack_ld_meas
    def ld_meas_recover_action(actor: LaneDetection):
        actor._get_pos = normal_ld_meas

    def change_ld_color(actor: LaneDetection, color: str):
        actor.marker_style["color"] = color
        actor.arrow_style["color"] = color
        actor.line_style["color"] = color

    # Lane detection results
    ld_meas = LaneDetection(ego, road.get_lines(), Point(10, 0),
                            normal_ld_meas, sample_period=0.1)
    change_ld_color(ld_meas, ld_traj_color)
    ld_meas.add_cb(FadeInOutCB(ld_title_time))
    ld_meas.add_cb(ActionCB(ld_meas_attack_action, ld_attack_time))
    ld_meas.add_cb(ChangeColorCB(ld_attack_time-1, 1,
                   Color(ld_traj_color), Color("red"), change_ld_color, False))
    ld_meas.add_cb(ActionCB(ld_meas_recover_action, mux_time-1))
    ld_meas.add_cb(ChangeColorCB(mux_time-1, 1, Color("red"),
                   Color(ld_traj_color), change_ld_color, False))
    scene.add_actor(ld_meas)

    # Use ld for localization
    def use_ld_for_loc(actor: Car):
        actor.controller.meas = ld_meas
    def use_msf_for_loc(actor: Car):
        actor.controller.meas = msf_meas
    ego.add_cb(ActionCB(use_ld_for_loc, ld_attack_time))
    ego.add_cb(ActionCB(use_msf_for_loc, fusion2ar_time+.5))
    ego.add_cb(ActionCB(use_ld_for_loc, detected_time))

    def change_legend_color(actor: Actor, color: str):
        actor.text_style["color"] = color
        actor.marker_style["color"] = color

    # LD measurement annotation
    ld_meas_legend = TrajLegend(
        "LD", Point(1, 14), marker_style=ld_meas.marker_style)
    ld_meas_legend.marker_style['linewidth'] = 3
    ld_meas_legend.marker_style['color'] = ld_traj_color
    ld_meas_legend.add_cb(FadeInOutCB(ld_title_time))
    ld_meas_legend.add_cb(ChangeColorCB(
        ld_attack_time-1, 1, Color(ld_traj_color), Color("red"),
        change_legend_color, False))
    ld_meas_legend.add_cb(ChangeColorCB(
        mux_time-1, 1, Color("red"), Color(ld_traj_color),
        change_legend_color, False))
    scene.add_actor(ld_meas_legend)

    #  # Real trajectory of ego vehicle
    #  real_meas = Trajectory(ego)
    #  real_meas.MARKER_SIZE = 40
    #  real_meas.ANIMATION_TIME = -1
    #  real_meas.marker_style["marker"] = "o"
    #  real_meas.add_cb(FadeInOutCB(real_start_time, msf_start_time))
    #  scene.add_actor(real_meas)

    #  # Real trajectory annotation
    #  real_meas_legend = TrajLegend(
        #  "Ground truth", Point(1, 12.5), marker_style=real_meas.marker_style)
    #  real_meas_legend.marker_style['color'] = gt_color
    #  real_meas_legend.MARKER_SIZE = 120
    #  real_meas_legend.add_cb(FadeInOutCB(real_start_time, msf_start_time))
    #  scene.add_actor(real_meas_legend)

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
        attack_time, 1, Color(legend_color), Color("red"), change_legend_color,
        False))
    scene.add_actor(msf_meas_legend)

    # Detect text box
    detect_text = Text("Attack detection", Point(7.3, 15), add_box=True)
    detect_text.text_style["size"] = box_text_size
    detect_text.add_cb(FadeInOutCB(detect_start_time+.5))
    scene.add_actor(detect_text)

    # Attack response text box
    attack_response_text_box = Text(
        "Attack response\n(e.g., safe in-lane stopping)",
        Point(ar_left, 15), add_box=True)
    attack_response_text_box.text_style["size"] = box_text_size
    attack_response_text_box.add_cb(FadeInOutCB(
        ar_box_time+1, mux_time, remove_after_fadeout=False))
    attack_response_text_box.add_cb(FadeInOutCB(detected_time))
    scene.add_actor(attack_response_text_box)

    # Fusion text box
    fusion_text_box = Text("Safety-driven fusion",
                           Point(6.1, 10), add_box=True)
    fusion_text_box.text_style["size"] = box_text_size
    fusion_text_box.add_cb(FadeInOutCB(fusion_time+1))
    scene.add_actor(fusion_text_box)

    # detect_polyline
    ld2detect_poly = PolyLine(
        Point(legend_right, 14.05), [Point(1, 0), Point(0, 1.15), Point(2.45, 0)], 1)
    ld2detect_poly.line_style["color"] = detect_color
    ld2detect_poly.add_cb(FadeInOutCB(detect_start_time))
    scene.add_actor(ld2detect_poly)

    def change_arrow_color(actor: Actor, color: str):
        actor.line_style["color"] = color
        actor.arrow_style["color"] = color

    msf2detect_poly = PolyLine(
        Point(legend_right, 12.5), [Point(2, 0), Point(0, 2.3), Point(1.45, 0)], 1)
    msf2detect_poly.line_style["color"] = detect_color
    msf2detect_poly.add_cb(FadeInOutCB(detect_start_time))
    msf2detect_poly.add_cb(ChangeColorCB(
        attack_time, 1,
        Color(msf2detect_poly.line_style["color"]),
        Color(attack_color), change_arrow_color))
    scene.add_actor(msf2detect_poly)

    # Attack response poly lines
    detect2ar_poly = PolyLine(
        Point(detect_right, 15), [Point(2.45, 0)], 1)
    detect2ar_poly_2 = copy.deepcopy(detect2ar_poly)
    detect2ar_poly.line_style["color"] = detect_color
    detect2ar_poly.add_cb(FadeInOutCB(ar_box_time, mux_time))
    scene.add_actor(detect2ar_poly)

    detect2ar_poly_2.line_style["color"] = detect_color
    detect2ar_poly_2.add_cb(FadeInOutCB(detected_time))
    scene.add_actor(detect2ar_poly_2)

    # Attack! text
    detect_attack_text = Text("Attack!", Point(detect_right, 15.5))
    detect_attack_text.text_style["color"] = "red"
    detect_attack_text.text_style["size"] = 24
    detect_attack_text.add_cb(FadeInOutCB(ar_box_time+1, mux_time))
    scene.add_actor(detect_attack_text)
    # No attack text
    detect_no_attack_text = Text("No attack", Point(detect_right, 15.5))
    detect_no_attack_text.text_style["color"] = "red"
    detect_no_attack_text.text_style["size"] = 22
    detect_no_attack_text.add_cb(FadeInOutCB(mux_time+1, attack_time))
    scene.add_actor(detect_no_attack_text)

    ld2ar_poly = PolyLine(Point(legend_right, 13.95),
                          [Point(9, 0), Point(0, -1), Point(4, 0), Point(0, 1.25)], 1)
    ld2ar_poly.line_style["color"] = sensor_direct_color
    ld2ar_poly.add_cb(FadeInOutCB(naive_ld2ar, fusion_time))
    ld2ar_poly.add_cb(ChangeColorCB(
        ld_attack_time-1, 1, Color(sensor_direct_color), Color("red"),
        change_arrow_color, False))
    ld2ar_poly.add_cb(ChangeColorCB(
        fusion_time-1, 1, Color("red"), Color(sensor_direct_color),
        change_arrow_color, False))
    scene.add_actor(ld2ar_poly)

    loc2ar_poly = PolyLine(Point(loc_left+1.2, 11.65), [Point(0, 2.55)], 1)
    loc2ar_poly.line_style["color"] = loc_color
    loc2ar_poly.add_cb(FadeInOutCB(detected_time))
    scene.add_actor(loc2ar_poly)

    fusion2ar = PolyLine(
        Point(fusion_right, 10), [Point(5.5, 0), Point(0, 4.3)], 1)
    fusion2ar.line_style["color"] = loc_color
    fusion2ar.add_cb(FadeInOutCB(fusion2ar_time, mux_time))
    scene.add_actor(fusion2ar)

    # fusion_polyline
    ld2fusion_poly = PolyLine(
        Point(legend_right, 14), [Point(1.5, 0), Point(0, -3.8), Point(.75, 0)], 1)
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
        Point(legend_right, 12.45), [Point(1, 0), Point(0, -2.65), Point(1.25, 0)], 1)
    msf2fusion_poly.line_style["color"] = loc_color
    msf2fusion_poly.add_cb(FadeInOutCB(fusion_time))
    msf2fusion_poly.add_cb(ChangeColorCB(
        attack_time, 1,
        Color(msf2fusion_poly.line_style["color"]),
        Color(attack_color), change_arrow_color))
    scene.add_actor(msf2fusion_poly)

    # Mux
    mux = Mux(Point(mux_left, 11.275))
    mux.add_cb(FadeInOutCB(mux_time))
    scene.add_actor(mux)

    # Localization_text
    localization_text = Text("Localization", Point(loc_left, 11.225), add_box=True)
    localization_text.text_style["size"] = box_text_size
    localization_text.add_cb(FadeInOutCB(localization_time))
    scene.add_actor(localization_text)

    # mux_polyline
    msf2mux_poly = PolyLine(Point(legend_right, 12.55),
                            [Point(mux_left-legend_right-.1, 0)], 1)
    msf2mux_poly.line_style["color"] = sensor_direct_color
    msf2mux_poly.add_cb(FadeInOutCB(mux_time))
    msf2mux_poly.add_cb(ChangeColorCB(
        attack_time, 1,
        Color(msf2mux_poly.line_style["color"]),
        Color(attack_color), change_arrow_color))
    scene.add_actor(msf2mux_poly)

    fusion2mux_poly = PolyLine(Point(fusion_right, 10),
                               [Point(mux_left-fusion_right-.1, 0)], 1)
    fusion2mux_poly.line_style["color"] = loc_color
    fusion2mux_poly.add_cb(FadeInOutCB(mux_time))
    scene.add_actor(fusion2mux_poly)

    detect2mux_poly = PolyLine(
        Point(detect_right, 15), [Point(mux_left-detect_right+0.5, 0), Point(0, -2.1)], 1)
    detect2mux_poly.line_style["color"] = detect_color
    detect2mux_poly.add_cb(FadeInOutCB(mux_time+1))
    scene.add_actor(detect2mux_poly)

    mux2localization_poly = PolyLine(
        Point(mux_right, 11.225), [Point(loc_left-mux_right-.35, 0)], 1)
    mux2localization_poly.line_style["color"] = sensor_direct_color
    mux2localization_poly.add_cb(FadeInOutCB(localization_time))
    mux2localization_poly.add_cb(ChangeColorCB(
        detected_time, 1,
        Color(mux2localization_poly.line_style["color"]),
        Color(loc_color), change_arrow_color))
    scene.add_actor(mux2localization_poly)

    # Attacker image
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
        "pics/signal.png", Point(4.8, 7.2), w=4, h=4, rotate_degree=230)
    spoofing_signal.texture.image_style["zorder"] = 99
    spoofing_signal.add_cb(
        ImageGrowCB(attack_time, attack_time+.2))
    scene.add_actor(spoofing_signal)

    # Detected text
    detected_text = Text("Attack detected!", Point(6.3, 16))
    detected_text.text_style["color"] = "red"
    detected_text.text_style["size"] = 26
    detected_text.add_cb(FadeInOutCB(detected_time-1))
    scene.add_actor(detected_text)

    #  # Use fusion text
    #  use_fusion_text = Text("Use safety-driven fusion", Point(loc_left, 10.5))
    #  use_fusion_text.text_style["color"] = "red"
    #  use_fusion_text.text_style["size"] = 18
    #  use_fusion_text.add_cb(FadeInOutCB(detected_time))
    #  scene.add_actor(use_fusion_text)

    #  # Slowing down text
    #  stopping_text = Text("In-lane stopping", Point(ar_left, 16))
    #  stopping_text.text_style["color"] = "red"
    #  stopping_text.text_style["size"] = 18
    #  stopping_text.add_cb(FadeInOutCB(detected_time))
    #  scene.add_actor(stopping_text)

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
        ("LD can be used for local localization, and the vehicle knows its position within the lane.",
         ld_title_time, msf_start_time),
        ("The first to use a local localization method (LD) to defend against attacks on global localization.\n"
         "$LD^3$ first cross-checks with MSF to detect attacks, and then performs safe in-lane stopping.",
         msf_start_time, naive_ld2ar),
        ("For localization, we can naively fully trust LD, but it's vulnerable to LD attacks.",
         naive_ld2ar, fusion_time),
        ("Instead, we design a novel safety-driven fusion based on aggressiveness of causing lane departure.",
         fusion_time, suspicious_explanation_time),
        ("No matter whether the attacker chooses to attack LD or MSF, the attack effect will be penalized\n"
         "to achieve safe in-lane stopping.",
         suspicious_explanation_time, mux_time),
        ("Without attack, results from MSF are used for localization.",
         mux_time, attack_time),
        ("With attack, fusion results are used for localization to slow down within the lane.",
         attack_time, float("inf")),
    ], Point(1, scene.camera.limits.y-1.5), typing_effect=False)
    for explanation in explanations.actors:
        explanation.text_style["size"] = 22
    scene.add_actor(explanations)

    #  scene.run(start_time=attack_time, end_time=attack_time+1)
    scene.run()
    scene.to_vid()
