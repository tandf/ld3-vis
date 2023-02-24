from Scene import Scene
from Point import Point
from Actor import *
from Controller import *


def scene2(video_dir: str, debug: bool = False, high_quality: bool = False):
    fps = 60 if high_quality else 10
    dpi = 100

    ld_title_time = 1
    ld_explanation_time = ld_title_time + 1
    ld_start_time = ld_explanation_time + 1
    real_start_time = ld_start_time + 1
    msf_start_time = real_start_time + 3
    detect_start_time = msf_start_time + 1
    slow_down_time = detect_start_time + 2
    fusion_explanation_time = slow_down_time + 3
    fusion_time = fusion_explanation_time + 1
    suspicious_explanation_time = fusion_time + 5
    suspicious_time1 = suspicious_explanation_time + 2
    suspicious_time2 = suspicious_explanation_time + 3
    suspicious_highlight_time = 2
    mux_time = suspicious_time2 + suspicious_highlight_time
    localization_time = mux_time + 2
    attack_time = localization_time + 2

    duration = attack_time + 4  # seconds

    scene = Scene(video_dir, "scene2", duration, fps, dpi=dpi, debug=debug)

    # Add road
    road = Road()
    scene.add_actor(road)

    # Ego vehicle
    egoController = PIDController(Point(15, 0), yref=0)
    scene.set_ego(Car(pos=Point(0, 0), controller=egoController))
    scene.ego.load_texture()
    scene.add_actor(scene.ego)

    # Lane detection results
    ld_meas = LaneDetection(scene.ego, road.get_lines(), Point(10, 0),
                            GetPos.gausian_meas(scale=Point(0, .1)),
                            sample_period=0.1)
    ld_meas.add_cb(FadeInOutCB(ld_start_time))
    scene.add_actor(ld_meas)

    def change_text_color(actor: Actor, color: str):
        actor.text_style["color"] = color

    # LD measurement annotation
    ld_meas_legend = TrajLegend(
        "LD", Point(1, 14), marker_style=ld_meas.marker_style)
    ld_meas_legend.marker_style['linewidth'] = 3
    ld_meas_legend.add_cb(FadeInOutCB(ld_start_time))
    ld_meas_legend.add_cb(ChangeColorCB(
        suspicious_time1, suspicious_highlight_time,
        Color(ld_meas_legend.text_style["color"]), Color("red"),
        change_text_color, True))
    scene.add_actor(ld_meas_legend)

    # Real trajectory of ego vehicle
    real_meas = Trajectory(scene.ego)
    real_meas.MARKER_SIZE = 40
    real_meas.ANIMATION_TIME = -1
    real_meas.marker_style["marker"] = "o"
    real_meas.add_cb(FadeInOutCB(real_start_time))
    scene.add_actor(real_meas)

    # Real trajectory annotation
    real_meas_legend = TrajLegend(
        "Ground truth", Point(1, 12.5), marker_style=real_meas.marker_style)
    real_meas_legend.MARKER_SIZE = 120
    real_meas_legend.add_cb(FadeInOutCB(real_start_time, msf_start_time))
    scene.add_actor(real_meas_legend)

    # MSF measurement of ego vehicle (add normal distribution errors)
    msf_meas = Trajectory(
        scene.ego, GetPos.gausian_meas(scale=Point(.2, .2)), .1)
    msf_meas.marker_style["color"] = "green"
    msf_meas.line_style["color"] = "green"
    msf_meas.add_cb(FadeInOutCB(msf_start_time))
    scene.add_actor(msf_meas)
    egoController.traj = msf_meas

    # MSF measurement annotation
    msf_meas_legend = TrajLegend(
        "MSF", Point(1, 12.5), marker_style=msf_meas.marker_style)
    msf_meas_legend.add_cb(FadeInOutCB(msf_start_time))
    msf_meas_legend.add_cb(ChangeColorCB(
        suspicious_time2, suspicious_highlight_time,
        Color(msf_meas_legend.text_style["color"]), Color("red"),
        change_text_color, True))
    scene.add_actor(msf_meas_legend)

    # Detect text box
    detect_text = Text("Cross checking", Point(8.8, 15), add_box=True)
    detect_text.text_style["size"] = 22
    detect_text.add_cb(FadeInOutCB(detect_start_time+1))
    scene.add_actor(detect_text)

    # Slow down text box
    slow_down_text = Text("Slow down?", Point(16.3, 15), add_box=True)
    slow_down_text.text_style["size"] = 22
    slow_down_text.add_cb(FadeInOutCB(slow_down_time+1))
    scene.add_actor(slow_down_text)

    # Fusion text box
    slow_down_text = Text("Fusion", Point(8.8, 10), add_box=True)
    slow_down_text.text_style["size"] = 22
    slow_down_text.add_cb(FadeInOutCB(fusion_time+1))
    scene.add_actor(slow_down_text)

    # detect_polyline
    detection_color = "#87CEFA"
    ld2detect_poly = PolyLine(
        Point(4, 14.05), [Point(1.5, 0), Point(0, 1.15), Point(3, 0)], 1)
    ld2detect_poly.line_style["color"] = detection_color
    ld2detect_poly.add_cb(FadeInOutCB(detect_start_time))
    scene.add_actor(ld2detect_poly)

    msf2detect_poly = PolyLine(
        Point(4, 12.55), [Point(3.5, 0), Point(0, 2.25), Point(1, 0)], 1)
    msf2detect_poly.line_style["color"] = detection_color
    msf2detect_poly.add_cb(FadeInOutCB(detect_start_time))
    scene.add_actor(msf2detect_poly)

    # Detect to slow down
    detect2slow_poly = PolyLine(Point(13.5, 15), [Point(2.5, 0)], 1)
    detect2slow_poly.line_style["color"] = detection_color
    detect2slow_poly.add_cb(FadeInOutCB(slow_down_time))
    scene.add_actor(detect2slow_poly)

    # fusion_polyline
    fusion_color = "#DDA0DD"
    ld2fusion_poly = PolyLine(
        Point(4, 14), [Point(2.5, 0), Point(0, -3.8), Point(2, 0)], 1)
    ld2fusion_poly.line_style["color"] = fusion_color
    ld2fusion_poly.add_cb(FadeInOutCB(fusion_time))
    scene.add_actor(ld2fusion_poly)

    msf2fusion_poly = PolyLine(
        Point(4, 12.5), [Point(1.5, 0), Point(0, -2.7), Point(3, 0)], 1)
    msf2fusion_poly.line_style["color"] = fusion_color
    msf2fusion_poly.add_cb(FadeInOutCB(fusion_time))
    scene.add_actor(msf2fusion_poly)

    # Mux
    mux = Mux(Point(14, 11.225))
    mux.add_cb(FadeInOutCB(mux_time))
    scene.add_actor(mux)

    # Localization_text
    localization_text = Text("Localization", Point(16.3, 11.225), add_box=True)
    localization_text.text_style["size"] = 22
    localization_text.add_cb(FadeInOutCB(localization_time))
    scene.add_actor(localization_text)

    # mux_polyline
    msf_direct_color = "black"
    msf2mux_poly = PolyLine(Point(4, 12.45), [Point(10, 0)], 1)
    msf2mux_poly.line_style["color"] = msf_direct_color
    msf2mux_poly.add_cb(FadeInOutCB(mux_time))
    scene.add_actor(msf2mux_poly)

    fusion2mux_poly = PolyLine(Point(11, 10), [Point(3, 0)], 1)
    fusion2mux_poly.line_style["color"] = fusion_color
    fusion2mux_poly.add_cb(FadeInOutCB(mux_time))
    scene.add_actor(fusion2mux_poly)

    detect2mux_poly = PolyLine(Point(13.5, 15), [Point(1, 0), Point(0, -2.2)], 1)
    detect2mux_poly.line_style["color"] = detection_color
    detect2mux_poly.add_cb(FadeInOutCB(mux_time+1))
    scene.add_actor(detect2mux_poly)

    def change_arrow_color(actor: Actor, color: str):
        actor.line_style["color"] = color
        actor.arrow_style["color"] = color

    mux2localization_poly = PolyLine(Point(15, 11.225), [Point(1, 0)], 1)
    mux2localization_poly.line_style["color"] = msf_direct_color
    mux2localization_poly.add_cb(FadeInOutCB(localization_time))
    mux2localization_poly.add_cb(ChangeColorCB(
        attack_time, 2,
        Color(mux2localization_poly.line_style["color"]),
        Color(fusion_color), change_arrow_color))
    scene.add_actor(mux2localization_poly)

    titles = TextList([
        ("Lane detection (LD)", ld_title_time, msf_start_time),
        (["", "$L$", "$D$", "${ }^3$"] +
         list(": A LD based defense"), msf_start_time, float('inf')),
    ], Point(1, scene.camera.limits.y-.2))
    for title in titles.actors:
        title.text_style["size"] = 48
    scene.add_actor(titles)

    explanations = TextList([
        ("LD can be used for local localization,\n"
         "and the vehicle knows its position within the lane.",
         ld_explanation_time, msf_start_time),
        ("We can use LD to cross check with MSF to detect attacks,\n"
         "and slow down to avoid accidents.",
         msf_start_time, fusion_explanation_time),
        ("For localization, we can naively fully trust LD,\n"
         "but that is vulnerable to LD attacks.\n"
         "Instead, we fuse MSF and LD based on suspiciousness.",
         fusion_explanation_time, suspicious_explanation_time),
        ("The fusion algorithm will assign high suspiciousness to\n"
         "the source that can lead to severe consequences.",
         suspicious_explanation_time, mux_time),
        ("Without attack, results from MSF is used as localization.",
         mux_time, attack_time),
        ("With attack, fusion results are used for localization\n"
         "to slow down within the lane.",
         attack_time, float("inf")),
    ], Point(1, scene.camera.limits.y-2), typing_effect=False)
    for explanation in explanations.actors:
        explanation.text_style["size"] = 24
    scene.add_actor(explanations)

    #  scene.run(start_time=mux_time-1)
    scene.run()
    scene.to_vid()