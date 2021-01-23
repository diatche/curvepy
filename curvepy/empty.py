import math
from .curve import Curve, MIN_STEP
from intervalpy import Interval

class Empty(Curve):

    def get_domain(self):
        return Interval.empty()

    def __init__(self):
        super().__init__(min_step=math.inf)

    def __repr__(self):
        return 'empty'

    def y(self, x):
        return None

    def d_y(self, x, forward=False, min_step=MIN_STEP, limit=None):
        return None

    def x(self, y):
        return None
        