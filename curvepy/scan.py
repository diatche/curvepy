import math
from .curve import Curve, MIN_STEP
from .constant import Constant
from intervalpy import Interval

class Scan(Curve):

    def get_domain(self):
        return self.curve.domain

    def __init__(self, func, tfm, min_step=MIN_STEP):
        super().__init__(min_step=min_step)
        self.curve = Curve.parse(func)
        self.tfm = tfm
        self.scan_start = None
        self.current = None
        self._observer_token = self.curve.add_observer(begin=self.begin_scan_update, end=self.end_scan_update, prioritize=True)

    def __del__(self):
        try:
            self.curve.remove_observer(self._observer_token)
        except Exception:
            pass

    def y(self, x):
        if not self.curve.domain.contains(x) and not self.domain.contains(x):
            return None
        self.scan(x)
        return self.scanned_y(x)

    def scanned_y(self, x):
        raise Exception("Not implemented")

    def continue_scan(self, x):
        return self.current < x

    def init_scan(self, x):
        if self.curve.domain.is_empty or self.curve.domain.is_negative_infinite:
            return x
        x0 = self.curve.domain.start
        if not self.domain.contains(x0):
            x0 = self.curve.x_next(x0, min_step=self.min_step)
        return x0

    def offset_scan(self, x):
        return x

    def reset_scan(self):
        self.scan_start = None
        self.current = None

    def scan(self, x0):
        x = self.offset_scan(x0)
        if self.scan_start is not None and x < self.scan_start:
            self.reset_scan()
        while self.current is None or self.continue_scan(x0):
            if self.current is None:
                self.scan_start = self.init_scan(x)
                current = self.scan_start
            else:
                current = self.x_next(self.current, min_step=self.min_step, limit=x0)
            if current is None or not self.curve.domain.contains(current):
                break
            if self.current is not None and current <= self.current:
                raise Exception('Next scan x value ({}) is smaller than or equal to the current scan x value ({}).'.format(current, self.current))
            self.tfm(current, self.curve.y(current))
            self.current = current

    def sample_points(self, domain=None, min_step=MIN_STEP, step=None):
        min_step = self.resolve_min_step(min_step)
        if domain is None:
            domain = self.domain
        else:
            domain = Interval.intersection([self.domain, domain])
        if domain.is_empty:
            return []
        elif domain.is_infinite:
            raise Exception("Cannot sample points on an infinite domain. Specify a finite domain.")
        self.scan(domain.start)
        self.scan(domain.end)
        return super().sample_points(domain=domain, min_step=min_step, step=step)

    def x_previous(self, x, min_step=MIN_STEP, limit=None):
        min_step = self.resolve_min_step(min_step)
        return self.curve.x_previous(x, min_step=min_step, limit=limit)

    def x_next(self, x, min_step=MIN_STEP, limit=None):
        min_step = self.resolve_min_step(min_step)
        return self.curve.x_next(x, min_step=min_step, limit=limit)

    def begin_scan_reset(self):
        self.reset_scan()
        self.begin_update(Interval.infinite())

    def end_scan_reset(self):
        self.end_update(Interval.infinite())

    def begin_scan_update(self, domain):
        domain = self._update_interval(domain)
        if self.current is not None:
            if domain.start < self.current or (domain.start == self.current and not domain.start_open):
                self.reset_scan()

        if self.current is not None and self.scan_start is not None and self.current < self.scan_start:
            self.reset_scan()

        self.begin_update(domain)

    def end_scan_update(self, domain):
        domain = self._update_interval(domain)
        self.end_update(domain)

    def _update_interval(self, domain):
        return Interval(domain.start, math.inf, start_open=domain.start_open, end_open=True)
