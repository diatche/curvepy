from .curve import Curve, MIN_STEP
from intervalpy import Interval

class Piecewise(Curve):

    def get_domain(self):
        return Interval.union(self.domains)

    def __init__(self, funcs, domains):
        """
        `domains` are assumed to be in ascending order and not overlapping.
        """
        super().__init__()
        if len(funcs) != len(domains):
            raise Exception("Must specify sub-domains for all sub-functions in a piecewise function")
        self.funcs = Curve.parse_many(funcs)
        self.domains = Interval.parse_many(domains)
        unique_funcs = list(set(list(self.funcs)))
        self._observer_tokens = list(map(lambda f: f.add_observer(begin=self.begin_update, end=self.end_update, prioritize=True), unique_funcs))

    def __del__(self):
        for func, token in zip(self.funcs, self._observer_tokens):
            func.remove_observer(token)

    def y(self, x):
        for i in range(len(self.domains)):
            d = self.domains[i]
            if not d.contains(x, enforce_start=False):
                continue
            elif not d.contains(x, enforce_end=False):
                break
            f = self.funcs[i]
            return f.y(x)
        return None
    
    def x_previous(self, x, min_step=MIN_STEP, limit=None):
        # FIXME: infinite funcs don't work (unit tests disabled)
        min_step = self.resolve_min_step(min_step)
        if not self.domain.contains(x - min_step, enforce_end=False):
            return None
        x_map = map(lambda f: f.x_previous(x, min_step=min_step, limit=limit), self.funcs)
        x_map_d = zip(x_map, self.domains)
        def x_previous_f(z):
            x, d = z
            return d.contains(x)
        z = max(filter(x_previous_f, x_map_d), default=None)
        x1 = z[0] if z is not None else None
        if x1 is None and self.domains[0].contains(x):
            return self.domains[0].start

    def x_next(self, x, min_step=MIN_STEP, limit=None):
        # FIXME: infinite funcs don't work (unit tests disabled)
        min_step = self.resolve_min_step(min_step)
        if not self.domain.contains(x + min_step, enforce_end=False):
            return None
        x_map = map(lambda f: f.x_next(x, min_step=min_step, limit=limit), self.funcs)
        x_map_d = zip(x_map, self.domains)
        def x_next_f(z):
            x, d = z
            return d.contains(x)
        z = min(filter(x_next_f, x_map_d), default=None)
        x1 = z[0] if z is not None else None
        if x1 is None and self.domains[-1].contains(x):
            return self.domains[-1].end
