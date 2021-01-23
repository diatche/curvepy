import math
from .curve import Curve, MIN_STEP
from intervalpy import Interval

class Sin(Curve):

    @property
    def frequency(self):
        return self.x_coef / math.pi * 0.5

    @property
    def period(self):
        return math.pi * 2 / self.x_coef

    def get_domain(self):
        return Interval.infinite()

    def __init__(self, amplitude=None, frequency=None, period=None, phase=0, phase_x=None):
        super().__init__()
        self.set(amplitude=amplitude, frequency=frequency, period=period, phase=phase, phase_x=phase_x)
    
    def set(self, amplitude=None, frequency=None, period=None, phase=0, phase_x=None):
        self.begin_update(self.domain)
        self.amplitude = amplitude
        self.phase = phase

        self.x_coef = None
        if period is not None:
            frequency = 1.0 / period
        if frequency is not None:
            self.x_coef = frequency * math.pi * 2.0
        if phase_x is not None:
            self.phase = phase_x * self.x_coef

        if self.amplitude is None or self.x_coef is None or self.phase is None:
            raise Exception("Invalid sin function description")
        self.end_update(self.domain)

    def y(self, x):
        return self.amplitude * math.sin(self.x_coef * x + self.phase)

    def d_y(self, x, forward=False, min_step=MIN_STEP, limit=None):
        return self.amplitude * math.cos(self.x_coef * x + self.phase)
        