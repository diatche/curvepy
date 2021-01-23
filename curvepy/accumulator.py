import math
from .scan import Scan
from .points import Points
from .curve import MIN_STEP
from intervalpy import Interval

class Accumulator(Scan):

    def __init__(
            self,
            func,
            tfm,
            interpolation=None,
            uniform=True,
            min_step=MIN_STEP):
        assert callable(tfm)
        self.accumulated_points = Points([], interpolation=interpolation, uniform=uniform)
        self.accumulator_transform = tfm
        super().__init__(func, self._accumulate, min_step=min_step)

    def scanned_y(self, x):
        return self.accumulated_points.y(x)

    def reset_scan(self):
        super().reset_scan()
        self.accumulated_points.reset()

    def x_previous(self, x, min_step=MIN_STEP, limit=None):
        min_step = self.resolve_min_step(min_step)
        return self.accumulated_points.x_previous(x, min_step=min_step, limit=limit) or self.curve.x_previous(x, min_step=min_step, limit=limit)

    def x_next(self, x, min_step=MIN_STEP, limit=None):
        min_step = self.resolve_min_step(min_step)
        return self.accumulated_points.x_next(x, min_step=min_step, limit=limit) or self.curve.x_next(x, min_step=min_step, limit=limit)

    def begin_update(self, domain):
        self.accumulated_points.reset(domain)
        super().begin_update(domain)

    def _accumulate(self, x, y):
        if self.accumulated_points.domain.is_empty:
            last_y = None
        else:
            last_x = self.accumulated_points.domain.end
            assert last_x < x
            last_y = self.accumulated_points.y(last_x)
        new_y = self.accumulator_transform(x, y, last_y)
        self.accumulated_points.append((x, new_y))
