from .curve import Curve, MIN_STEP
from intervalpy import Interval

class Generic(Curve):

    def get_domain(self):
        return self._domain

    def __init__(self, y_func, domain=None, min_step=MIN_STEP):
        super().__init__(min_step=min_step)
        self.y_func = y_func
        self._domain = Interval.parse(domain) if domain is not None else Interval.infinite()

    def y(self, x):
        if not self.domain.contains(x):
            return None
        return self.y_func(x)