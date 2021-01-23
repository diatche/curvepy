import math
from .curve import Curve, MIN_STEP
from intervalpy import Interval


class Line(Curve):

    def get_domain(self):
        return Interval.infinite()

    def __init__(self, const=None, slope=None, p1=None, p2=None, points=None):
        super().__init__(min_step=math.inf)
        self.ref_point = (0, 0)
        self.slope = 0
        self.set(const=const, slope=slope, p1=p1, p2=p2, points=points)

    @property
    def const(self):
        return self.y(0)

    def __repr__(self):
        try:
            if self.ref_point[0] == 0:
                x = 'x'
            else:
                x = f'(x - {self.ref_point[0]})'
            if self.ref_point[1] == 0:
                _y = ''
            else:
                _y = f' + {self.ref_point[1]}'

            return f'{x} * {self.slope}{_y}'
        except Exception as e:
            return super().__repr__() + f'({e})'

    def set(self, const=None, slope=None, p1=None, p2=None, points=None):
        ref_point = (0, const)
        slope = slope
        if points is not None:
            p1 = points[0]
            p2 = points[1]
        if p1 is None:
            p1 = ref_point
        else:
            ref_point = (p1[0], p1[1])
        if p2 is not None:
            if p2[0] != p1[0]:
                slope = (p2[1] - p1[1]) / (p2[0] - p1[0])
            elif p2[1] >= p1[1]:
                slope = math.inf
            else:
                slope = -math.inf
        if ref_point[0] is None or ref_point[1] is None:
            raise Exception("Line requires a constant or reference point")
        if slope is None:
            raise Exception("Line requires a slope")

        if ref_point[0] == self.ref_point[0] and ref_point[1] == self.ref_point[1] and slope == self.slope:
            return

        self.begin_update(self.domain)
        self.ref_point = ref_point
        self.slope = slope
        self.end_update(self.domain)

    def y(self, x):
        return self.ref_point[1] + self.slope * (x - self.ref_point[0])

    def d_y(self, x, forward=False, min_step=MIN_STEP, limit=None):
        return self.slope

    def x(self, y):
        return self.ref_point[0] + (y - self.ref_point[1]) / self.slope

    def partial_integration(self, a, b):
        # f(x) = slope / 2 * x ^ 2 + const * x + K
        # integral = f(b) - f(a)
        if a is not None and a == b:
            return 0
        const = self.const
        slope = self.slope
        ia = slope * 0.5 * a ** 2 + const * a
        ib = slope * 0.5 * b ** 2 + const * b
        return ib - ia
