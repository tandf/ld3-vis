from Point import Point
from Actor import *


class Controller:
    def __init__(self, speed: Point) -> None:
        self.speed = speed

    def get_speed(self) -> Point:
        return self.speed


class PIDController(Controller):
    def __init__(self, speed: Point, yref: int,
                 trajectory: Trajectory = None) -> None:
        super().__init__(speed)

        self.traj = trajectory
        self.yref = yref

        self.e_cum = 0
        self.kp = .5
        self.ki = 0
        self.kd = 0

    def get_speed(self) -> Point:
        assert self.traj
        if self.traj.trajectory:
            ymeas = self.traj.trajectory[-1].y
            error = (self.yref - ymeas)
            self.e_cum = self.e_cum * 0.7 + error

            self.speed.y = self.kp * error + self.ki * self.e_cum

        return self.speed

