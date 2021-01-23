import math
from .curve import Curve, MIN_STEP
from .points import Points
from .integral import Integral
from intervalpy import Interval

class SMA(Integral):

    """
    Only forward direction is supported.
    """

    def get_domain(self):
        d = self.curve.domain
        if d.is_empty:
            return Interval.empty()
        if self.period is not None:
            x = self.curve.x_previous(d.start + self.period, min_step=self.min_step)
            if x is None:
                p = self.period
            else:
                p = x - d.start
        elif self.degree is not None:
            x = d.start
            for _ in range(self.degree - 1):
                x = self.curve.x_next(x, min_step=self.min_step)
                if x is None:
                    return Interval.empty()
            p = x - d.start
        else:
            raise Exception('Bad SMA configuration')
        d_start = d.start + p
        if math.isnan(d_start) or d_start > d.end:
            return Interval.empty()
        return Interval.closed(d_start, d.end)

    def __init__(self, func, degree, is_period=True, uniform=True, min_step=MIN_STEP):
        super().__init__(func, uniform=uniform, min_step=min_step)
        self.degree = None
        self.period = None
        if is_period:
            self.period = degree
            if self.period is None or self.period <= 0:
                raise Exception('SMA period must be a positive number')
        else:
            self.degree = int(degree)
            if self.degree <= 0:
                raise Exception('SMA degree must be a positive integer')

    def __repr__(self):
        try:
            return f'{self.curve}.sma({self.degree or self.period})'
        except Exception as e:
            return super().__repr__() + f'({e})'

    def init_scan(self, x):
        return x
        # if self.curve.domain.is_empty or self.curve.domain.is_negative_infinite:
        #     return x
        # x0 = self.curve.x_previous(x, min_step=self.min_step)
        # if not self.domain.contains(x0):
        #     x0 = self.curve.x_next(self.curve.domain.start, min_step=self.min_step)
        # return x0

    def offset_scan(self, x):
        return self._sma_start(x)

    def y(self, x):
        # Return the average slope as the SMA
        if not self.domain.contains(x):
            return None

        # Get step
        x0 = self._sma_start(x)
        x1 = self._sma_end(x0)
        if x0 == x or x0 == x1:
            # SMA step is smaller than or equal to the underlying step
            return self.curve.y(x)

        # Values must be accessed in ascending order
        y0 = super().y(x0)
        if y0 is None:
            return None
        y1 = super().y(x1)
        if y1 is None:
            return None

        sma1 = (y1 - y0) / (x1 - x0)
        if x == x1:
            return sma1

        # Handle offset
        if x > x1:
            x2 = self.curve.x_next(x1, min_step=self.min_step)
            if x2 == x:
                return sma1
            sma2 = self.y(x2)
            if sma2 is None:
                return None
            u = (x - x1) / (x2 - x1)
            sma = u * sma2 + (1 - u) * sma1
        else:
            x01 = self.curve.x_previous(x1, min_step=self.min_step)
            if x01 == x:
                return sma1
            sma01 = self.y(x01)
            if sma01 is None:
                return None
            u = (x - x01) / (x1 - x01)
            sma = u * sma01 + (1 - u) * sma1
            return sma
        return sma

    def _sma_start(self, x):
        if self.period is not None:
            x0 = self.curve.x_next(x - self.period, min_step=self.min_step)
        elif self.degree is not None:
            x0 = x
            for _ in range(0, self.degree - 1):
                x1 = self.curve.x_previous(x0, min_step=self.min_step)
                if x1 is None:
                    return x0
                x0 = x1
        else:
            raise Exception('Bad SMA configuration')
        return x0

    def _sma_end(self, x):
        if self.period is not None:
            x0 = self.curve.x_previous(x + self.period, min_step=self.min_step)
        elif self.degree is not None:
            x0 = x
            for _ in range(0, self.degree - 1):
                x1 = self.curve.x_next(x0, min_step=self.min_step)
                if x1 is None:
                    return x0
                x0 = x1
        else:
            raise Exception('Bad SMA configuration')
        return x0
