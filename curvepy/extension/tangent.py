from .extension import Extension
from ..line import Line
from intervalpy import Interval

class TangentExtension(Extension):

    """
    Extends an end of a function with a line using its edge tangents.
    """

    name = "tangent"

    def __init__(self, func, regression_degree=None, regression_period=None, **kwargs):
        self.regression_degree = None
        self.regression_period = None
        if regression_degree is not None:
            self.regression_degree = int(regression_degree)
            assert self.regression_degree > 0
        if regression_period is not None:
            self.regression_period = float(regression_period)
            assert self.regression_period > 0
        assert self.regression_degree is None or self.regression_period is None
        super().__init__(func, **kwargs)

    def update_extension(self):
        if self.start:
            x = self.curve.domain.start
            if x is not None and self.curve.domain.start_open and self.curve.domain.contains(x + self.min_step):
                x += self.min_step
            y = None
            d_y = None
            if self.regression_degree is not None:
                x1 = x
                for i in range(self.regression_degree):
                    x1 = self.curve.x_next(x1, min_step=self.min_step)
                domain = Interval(x, x1)
                tangent = self.curve.regression(domain, min_step=self.min_step)
                if tangent is not None:
                    y = tangent.y(x)
                    d_y = tangent.slope
            elif self.regression_period is not None:
                domain = Interval(x, x + self.regression_period)
                tangent = self.curve.regression(domain, min_step=self.min_step)
                if tangent is not None:
                    y = tangent.y(x)
                    d_y = tangent.slope
            else:
                y = self.curve.y(x)
                d_y = self.curve.d_y(x, forward=True)

            self.start_valid = y is not None and d_y is not None
            if self.start_valid:
                self.update_extension_func(self.start_func, x, y, d_y)

        if self.end:
            x = self.curve.domain.end
            if x is not None and self.curve.domain.end_open and self.curve.domain.contains(x - self.min_step):
                x -= self.min_step
            y = None
            d_y = None
            if self.regression_degree is not None:
                x0 = x
                for i in range(self.regression_degree):
                    x0 = self.curve.x_previous(x0, min_step=self.min_step)
                domain = Interval(x0, x)
                tangent = self.curve.regression(domain, min_step=self.min_step)
                if tangent is not None:
                    y = tangent.y(x)
                    d_y = tangent.slope
            elif self.regression_period is not None:
                domain = Interval(x - self.regression_period, x)
                tangent = self.curve.regression(domain, min_step=self.min_step)
                if tangent is not None:
                    y = tangent.y(x)
                    d_y = tangent.slope
            else:
                y = self.curve.y(x)
                d_y = self.curve.d_y(x, forward=False)

            self.end_valid = y is not None and d_y is not None
            if self.end_valid:
                self.update_extension_func(self.end_func, x, y, d_y)

    def create_extension_func(self, start=False):
        return Line(const=0, slope=0)

    def update_extension_func(self, func, x, y, dy):
        func.set(p1=(x, y), slope=dy)
