from .accumulator import Accumulator
from .line import Line
from .points import Points
from .curve import MIN_STEP
from intervalpy import Interval


class Integral(Accumulator):

    def __init__(self, func, const=0, interpolation=None, **kwargs):
        super().__init__(func, self._integral_scan, interpolation=None, **kwargs)
        self.const = const
        self.integral_interpolation = interpolation or Points.interpolation.linear
        self._line = Line(const=0, slope=0)

    def scanned_y(self, x):
        y = super().scanned_y(x)
        if y is None:
            return y
        return y + self.const

    def _integral_scan(self, x, y, integral_sum):
        if y is None:
            return integral_sum
        if integral_sum is None:
            integral_sum = 0.0

        x0 = self.accumulated_points.x_previous(x)
        if x0 is not None:
            y0 = self.curve.y(x0)
        else:
            y0 = None

        if y0 is not None:
            interpolation = self.integral_interpolation
            if interpolation == Points.interpolation.linear:
                p1 = (x0, y0)
                p2 = (x, y)
            elif interpolation == Points.interpolation.previous:
                p1 = (x0, y0)
                p2 = (x, y0)
            elif interpolation == Points.interpolation.next:
                p1 = (x0, y)
                p2 = (x, y)
            else:
                raise Exception(f'Unsupported interpolation: {self.interpolation}')
            self._line.set(p1=p1, p2=p2)
            area = self._line.partial_integration(x0, x)
            integral_sum += area

        return integral_sum
