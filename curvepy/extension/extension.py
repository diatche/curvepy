from ..curve import Curve, MIN_STEP
from intervalpy import Interval

class Extension(Curve):

    """
    Extends ends of a function.
    """

    name = ""

    def get_domain(self):
        self._update_extension_interval()
        return Interval.union([self.curve.domain, self.extension_interval])

    def __init__(self, func, start=True, end=True, uniform=True, raise_on_empty=False, min_step=MIN_STEP):
        super().__init__(min_step=min_step)
        self.curve = Curve.parse(func)

        if self.curve.domain.is_negative_infinite:
            start = False
        if self.curve.domain.is_positive_infinite:
            end = False

        self.start = start
        self.end = end
        self.start_valid = True
        self.end_valid = True
        self.uniform = uniform
        self.raise_on_empty = raise_on_empty
        self.extension_interval = Interval.empty()
        self._extension_stale = True
        self._extension_interval_stale = True
        self.curve.add_observer(begin=self.begin_extension_update, end=self.end_extension_update, prioritize=True)
        self.start_func = None
        self.end_func = None
        if self.start:
            self.start_func = self.create_extension_func(start=True)
            self.start_func.add_observer(self, begin=self.begin_update, end=self.end_update)
        if self.end:
            self.end_func = self.create_extension_func(start=False)
            self.end_func.add_observer(self, begin=self.begin_update, end=self.end_update)

    def __del__(self):
        self.curve.remove_observer(self)

    def __repr__(self):
        try:
            vals = [type(self).__name__]
            if self.start:
                vals.append('start')
            if self.end:
                vals.append('end')
            return f'{self.curve}.extension({", ".join(vals)})'
        except Exception as e:
            return super().__repr__() + f'({e})'

    def update_extension(self):
        """
        Subclasses should override this method and refresh the extension.
        """
        pass

    def update_extension_interval(self):
        """
        Subclasses should override this method and refresh the extension domain if needed.
        """
        pass

    def create_extension_func(self, start=False):
        raise Exception('Not implemented')

    def y_extension(self, x):
        """
        Return the value of the extension for a given `x` value.
        """
        if self.curve.domain.is_empty:
            return None
        if self.start and x <= self.curve.domain.start:
            return self.start_func.y(x)
        if self.end and x >= self.curve.domain.end:
            return self.end_func.y(x)
        return None

    def y(self, x):
        if self.curve.domain.contains(x):
            return self.curve.y(x)
        self._update_extension_if_needed()
        if self.extension_interval.contains(x):
            return self.y_extension(x)
        return None

    def x_previous(self, x, min_step=MIN_STEP, limit=None):
        x1 = self.curve.x_previous(x, min_step=min_step)
        if x1 is None and self.start:
            # Keep returning extension with same step
            x0 = self.curve.x_next(self.curve.domain.start, min_step=min_step, limit=limit)
            if x0 is None:
                return None
            step = x0 - self.curve.domain.start
            x1 = x - step
        return x1

    def x_next(self, x, min_step=MIN_STEP, limit=None):
        x1 = self.curve.x_next(x, min_step=min_step)
        if x1 is None and self.end:
            # Keep returning extension with same step
            x0 = self.curve.x_previous(self.curve.domain.end, min_step=min_step, limit=limit)
            if x0 is None:
                return None
            step = self.curve.domain.end - x0
            x1 = x + step
        return x1

    def is_in_extension(self, x):
        domain = Interval.parse(x)
        return (self.start and domain <= self.extension_interval) or \
            (self.end and domain >= self.extension_interval)

    def begin_extension_update(self, domain):
        if self.is_in_extension(domain):
            self.begin_update(self.extension_interval)
        else:
            self.begin_update(domain)

    def end_extension_update(self, domain):
        if self.is_in_extension(domain):
            self._extension_stale = True
            self._update_extension_interval()
            self.end_update(self.extension_interval)
        else:
            self.end_update(domain)

    def _update_extension_interval(self):
        if not self._extension_interval_stale:
            return
        self._extension_interval_stale = False
        if self._extension_stale:
            self._update_extension_if_needed()

        if self.start and self.start_valid and self.end and self.end_valid:
            self.extension_interval = Interval.union([self.start_func.domain, self.end_func.domain])
        elif self.start and self.start_valid:
            self.extension_interval = Interval.intersection([self.start_func.domain, self.curve.domain.get_lt()])
        elif self.end and self.end_valid:
            self.extension_interval = Interval.intersection([self.end_func.domain, self.curve.domain.get_gt()])
        else:
            self.extension_interval = Interval.empty()
        self.update_extension_interval()
        if (self.start and not self.extension_interval.is_negative_infinite) or (self.end and not self.extension_interval.is_positive_infinite):
            if self.raise_on_empty:
                raise Exception('Unable to extend func')
            
    def _update_extension_if_needed(self):
        if not self._extension_stale:
            return
        self._extension_stale = False
        self._extension_interval_stale = True

        self.update_extension()
        if (self.start and not self.extension_interval.is_negative_infinite) or (self.end and not self.extension_interval.is_positive_infinite):
            if self.raise_on_empty:
                raise Exception('Unable to extend func')
        self._update_extension_interval()
