#! /bin/env python3

from __future__ import annotations
import os

from scene1 import scene1
from scene2 import scene2


def main():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    video_dir = os.path.join(dir_path, "videos")

    if not os.path.isdir(video_dir):
        os.mkdir(video_dir)

    debug = False
    high_quality = True

    scene1(video_dir, debug=debug, high_quality=high_quality)
    #  scene2(video_dir, debug=debug, high_quality=high_quality)


if __name__ == "__main__":
    main()
