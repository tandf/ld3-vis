from Point import Point
import copy


class Controller:
    def __init__(self, speed: Point) -> None:
        self.speed = copy.deepcopy(speed)

    def get_speed(self) -> Point:
        return self.speed


class PIDController(Controller):
    def __init__(self, speed: Point, yref: int, meas=None) -> None:
        super().__init__(speed)

        self.meas = meas
        self.yref = yref

        self.e_cum = 0
        self.kp = 0.7
        self.ki = 0.1
        self.kd = 0

    def get_speed(self) -> Point:
        assert self.meas
        assert hasattr(self.meas, "get_recent_meas")
        meas = self.meas.get_recent_meas()
        if meas:
            ymeas = meas.y
            error = (self.yref - ymeas)
            self.e_cum = self.e_cum * 0.7 + error

            self.speed.y = self.kp * error + self.ki * self.e_cum

        return self.speed

