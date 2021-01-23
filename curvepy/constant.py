import math
from .curve import Curve, MIN_STEP
from intervalpy import Interval

class Constant(Curve):

    @property
    def value(self):
        return self._value

    @classmethod
    def zero(cls):
        return _zero

    @value.setter
    def value(self, value):
        if value == self._value:
            return
        self.begin_update(self.domain)
        self._value = value
        self.end_update(self.domain)

    def get_domain(self):
        return self._const_interval

    def __init__(self, y, domain=None):
        super().__init__(min_step=math.inf)
        self._value = y
        if domain is not None:
            domain = Interval.parse(domain)
        else:
            domain = Interval.infinite()
        self._const_interval = domain

    def __repr__(self):
        try:
            return str(self.value)
        except Exception as e:
            return super().__repr__() + f'({e})'

    def y(self, x):
        return self.value

    def d_y(self, x, forward=False, min_step=MIN_STEP, limit=None):
        return 0.0

    def x(self, y):
        if y == self.value:
            return 0.0
        return None

_zero = Constant(0)
