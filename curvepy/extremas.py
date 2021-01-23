import bisect
from .scan import Scan
from .curve import Curve, MIN_STEP
from intervalpy import Interval

class Extremas(Scan):

    # TODO: Extremas doesn't need to be a subclass of `Scan` as it only needs to find the local extrema about a point.

    def __init__(self, func, ref_func, min_deviation=0, min_step=MIN_STEP):
        self.ref_func = Curve.parse(ref_func)
        self.min_deviation = abs(min_deviation)
        self.extremas = []
        self.extrema_xs = []
        self.extrema_interval = Interval.empty()
        self.possible_extrema = None
        self.possible_extrema_phase = None
        self._did_update_extremas()
        super().__init__(func, self._extrema_scan, min_step=min_step)
        self._ref_observer_token = self.ref_func.add_observer(begin=self.begin_update, end=self.end_update)

    def __del__(self):
        self.ref_func.remove_observer(self._ref_observer_token)

    def scanned_y(self, x):
        if not self.extrema_interval.contains(x):
            return None
        if x == self.extrema_interval.start:
            return self.extremas[0][1]
        elif x == self.extrema_interval.end:
            return self.extremas[-1][1]
        i = bisect.bisect(self.extrema_xs, x)
        p1 = self.extremas[i - 1]
        p2 = self.extremas[i]
        u = (x - p1[0]) / (p2[0] - p1[0])
        return (1 - u) * p1[1] + u * p2[1]

    def continue_scan(self, x):
        if super().continue_scan(x):
            return True
        if not self.domain.contains(self.current):
            return False
        return not self.extrema_interval.contains(x, enforce_start=False)

    def x_previous(self, x, min_step=MIN_STEP, limit=None):
        min_step = self.resolve_min_step(min_step)
        if self.extrema_interval.contains(x - min_step):
            i = bisect.bisect_left(self.extrema_xs, x - min_step)
            x1 = self.extremas[i][0]
            if x1 > x - min_step:
                x1 = self.extremas[i - 1][0]
            return x1
        return self.curve.x_previous(x, min_step=min_step, limit=limit)

    def x_next(self, x, min_step=MIN_STEP, limit=None):
        min_step = self.resolve_min_step(min_step)
        if self.extrema_interval.contains(x + min_step):
            i = bisect.bisect_left(self.extrema_xs, x + min_step)
            x1 = self.extremas[i][0]
            if x1 < x + min_step:
                x1 = self.extremas[i + 1][0]
            return x1
        return self.curve.x_next(x, min_step=min_step, limit=limit)

    def begin_update(self, domain):
        super().begin_update(domain)
        # remove stale points
        for i in reversed(range(len(self.extremas))):
            x = self.extrema_xs[i]
            if domain.contains(x):
                self._remove_extrema_index(i)
            elif domain.start > x:
                break

        # scan from last extrema
        extrema_count = len(self.extremas)
        if extrema_count == 0:
            self.current = None
        else:
            last_extrema = self.extremas[-1]
            x = last_extrema[0]
            self.current = x
            self.possible_extrema = last_extrema
            self.possible_extrema_phase = last_extrema[1] - self.ref_func(x)

    def sample_points(self, domain=None, min_step=MIN_STEP, step=None):
        points = super().sample_points(domain=domain, min_step=min_step, step=step)
        return list(filter(lambda p: p[1] is not None, points))

    def _extrema_scan(self, x, y):
        if y is None:
            return
        y0 = self.ref_func(x)
        if y0 is None:
            return
        div = y / y0 - 1
        if abs(div) <= self.min_deviation:
            # function is too close to reference function
            return
        phase = y - y0
        if self.possible_extrema is None:
            self.possible_extrema = (x, y)
            self.possible_extrema_phase = phase
            return
        is_possible_extrema = False
        if self.possible_extrema_phase * phase < 0:
            # phase inflection
            self._confirm_extrema()
            is_possible_extrema = True
        elif (phase > 0 and y > self.possible_extrema[1]) or (phase < 0 and y < self.possible_extrema[1]):
            is_possible_extrema = True
        if is_possible_extrema:
            self.possible_extrema = (x, y)
            self.possible_extrema_phase = phase
    
    def _remove_extrema_index(self, i):
        del self.extremas[i]
        del self.extrema_xs[i]
        self._did_update_extremas()

    def _confirm_extrema(self):
        extrema = self.possible_extrema

        self.extremas.append(extrema)
        self.extrema_xs.append(extrema[0])
        self._did_update_extremas()

    def _did_update_extremas(self):
        self.possible_extrema = None
        self.possible_extrema_phase = None

        if len(self.extremas) == 0:
            self.extrema_interval = Interval.empty()
        else:
            self.extrema_interval = Interval(self.extrema_xs[0], self.extrema_xs[-1], start_open=False, end_open=False)

    def _i(self, x):
        if not self.extrema_interval.contains(x):
            return None
        if x == self.extrema_interval.start:
            return 0
        elif x == self.extrema_interval.end:
            return len(self.extremas) - 1
        i = bisect.bisect(self.extrema_xs, x)
        p1 = self.extremas[i - 1]
        p2 = self.extremas[i]
        u = (x - p1[0]) / (p2[0] - p1[0])
        return i + u
