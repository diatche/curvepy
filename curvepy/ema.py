import math
from .accumulator import Accumulator
from .curve import Curve, MIN_STEP
from intervalpy import Interval

class EMA(Accumulator):
    """
    Only forward direction is supported.
    """

    # TODO: investigate difference between regular EMA and irregular EMA

    def __init__(self, func, degree, is_period=True, init=None, min_step=MIN_STEP, uniform=True):
        self.alpha = None
        self.period = None
        self.init_func = Curve.parse(init) if init is not None else None
        if is_period:
            self.period = degree
        else:
            self.alpha = degree
        super().__init__(func, self._ema_scan, min_step=min_step, uniform=uniform)

    def __repr__(self):
        try:
            return f'{self.curve}.ema({self.alpha or self.period})'
        except Exception as e:
            return super().__repr__() + f'({e})'

    # TODO: EMA doesn't have to initialise from the start of the underlying function
    # def init_scan(self, x):
    #     if self.period is not None:
    #         period = self.period
    #     elif self.alpha is not None:
    #         period = 1 / self.alpha
    #     else:
    #         raise Exception('Bad SMA configuration')       
    #     return self.curve.x_next(x - period, min_step=self.min_step)

    def _ema_scan(self, x, y, ema):
        if y is None:
            return ema
        if ema is None:
            if self.init_func is not None:
                return self.init_func.y(x)
            else:
                return y
        if self.period is not None:
            # TODO: use geometric mean instead of arithmetic?
            x0 = self.curve.x_previous(x, min_step=self.min_step)
            a = abs((x - x0) / self.period)
            return ema + a * (y - ema)
        elif self.alpha is not None:
            return ema + self.alpha * (y - ema)


# # Reference: http://www.thalesians.com/archive/public/academic/finance/papers/Zumbach_2000.pdf
# x0 = self.x_previous(x, min_step=self.min_step)
# y0 = self.curve(x0)
# x_delta = abs(x - x0)
# a = abs(x_delta / self.period)
# u = math.exp(-a)
# v = (1 - u) / a
# return u * ema + (v - u) * y0 + (1 - v) * y