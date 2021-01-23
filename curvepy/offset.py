import math
from .curve import Curve, MIN_STEP
from intervalpy import Interval
from pyduration import Duration


class Offset(Curve):

    """
    Offset a function on the x-axis by a constant.
    """

    def get_domain(self):
        return self._offset_interval(self.curve.domain)

    def __init__(self, func, offset, duration=None):
        super().__init__()
        self.curve = Curve.parse(func)
        self.offset = offset
        self.duration = None
        if duration is not None:
            self.duration = Duration.parse(duration)
            if type(self.offset) != int:
                raise Exception('Offset must be an interger when duration is defined')
        self._observer_token = self.curve.add_observer(
            begin=self.begin_offset_update, end=self.end_offset_update, prioritize=True)

    def __del__(self):
        self.curve.remove_observer(self._observer_token)

    def __repr__(self):
        try:
            return f'{self.curve}.offset({self.offset})'
        except Exception as e:
            return super().__repr__() + f'({e})'

    def y(self, x):
        return self._interpolated_func(self.curve.y, x)

    def d_y(self, x, **kwargs):
        return self._interpolated_func(self.curve.d_y, x, **kwargs)

    def _interpolated_func(self, f, x, **kwargs):
        x0 = self._unoffset_x(x, floor=True)
        x1 = self._unoffset_x(x, floor=False)
        if x0 is None or x1 is None or not self.curve.domain.contains(x0) or not self.curve.domain.contains(x1):
            return None
        if x0 == x1:
            return f(x0, **kwargs)
        y0 = f(x0, **kwargs)
        y1 = f(x1, **kwargs)

        if y0 is None or y1 is None:
            return None
        
        _x0 = self._offset_x(x0, floor=True)
        _x1 = self._offset_x(x1, floor=False)
        u = (x - _x0) / (_x1 - _x0)
        y = y0 * (1 - u) + y1 * u
        return y

    def x_previous(self, x, min_step=MIN_STEP, limit=None):
        x = self._unoffset_x(x, floor=False)
        if x is None:
            return None
        if self.duration:
            x1 = self.duration.previous(x)
        else:
            x1 = self.curve.x_previous(x, min_step=min_step, limit=limit)
        if x1 is None or not self.curve.domain.contains(x1):
            return None
        return self._offset_x(x1, floor=False)

    def x_next(self, x, min_step=MIN_STEP, limit=None):
        x = self._unoffset_x(x, floor=True)
        if x is None:
            return None
        if self.duration:
            x1 = self.duration.next(x)
        else:
            x1 = self.curve.x_next(x, min_step=min_step, limit=limit)
        if x1 is None or not self.curve.domain.contains(x1):
            return None
        return self._offset_x(x1, floor=True)

    def begin_offset_update(self, domain):
        self.begin_update(self._offset_interval(domain))

    def end_offset_update(self, domain):
        self.end_update(self._offset_interval(domain))

    def _offset_x(self, x, floor=False):
        if x is None or math.isinf(x):
            return x
        if self.duration is None:
            return x + self.offset
        else:
            return self._res_step(x, self.offset, floor=floor)

    def _unoffset_x(self, x, floor=False):
        if x is None or math.isinf(x):
            return x
        if self.duration is None:
            return x - self.offset
        else:
            return self._res_step(x, -self.offset, floor=floor)

    def _res_step(self, x, count, floor=False):
        if count == 0:
            return x
        if floor:
            x = self.duration.floor(x)
        else:
            x = self.duration.ceil(x)
        return self.duration.step(x, count=count)

    def _offset_interval(self, domain, floor=False):
        start = self._offset_x(domain.start, floor=floor)
        end = self._offset_x(domain.end, floor=floor)
        if start is None and end is None:
            return Interval.empty()
        elif start is None:
            return Interval(start, end, start_open=False, end_open=domain.end_open)
        elif end is None:
            return Interval(start, end, start_open=domain.start_open, end_open=False)
        else:
            return Interval(start, end, start_open=domain.start_open, end_open=domain.end_open)
