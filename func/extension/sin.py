import math
from .tangent import TangentExtension
from ..sin import Sin

class SinExtension(TangentExtension):

    """
    Extends an end of a function with a sine wave using its edge tangents.
    """

    name = "sin"

    def __init__(self, func, period=0, **kwargs):
        self.period = float(period)
        assert self.period > 0
        super().__init__(func, **kwargs)

    def create_extension_func(self, start=False):
        return Sin(amplitude=0, period=self.period)

    def update_extension_func(self, sin, x, y, dy):
        # angle
        x_coef = 2 * math.pi / self.period
        angle = x_coef * x

        # phase
        num = x_coef * y * math.cos(angle) - dy * math.sin(angle)
        den = x_coef * y * math.sin(angle) + dy * math.cos(angle)
        phase = math.atan2(num, den)

        # amplitude
        if (angle + phase) % math.pi != 0:
            amplitude = y / math.sin(angle + phase)
        else:
            amplitude = dy / (x_coef * math.cos(angle + phase))

        sin.set(amplitude=amplitude, period=self.period, phase=phase)
