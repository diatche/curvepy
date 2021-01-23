import math
import weakref
import inspect
import arrow
import numpy as np
from numbers import Number
from collections.abc import Sequence, Mapping
from intervalpy import Interval
from .const import GOLD
from . import util

MIN_STEP = 1e-5

# TODO: Implement Duration and use its next ad previous methods
# Or make a super class which is not tied to a time interval.

_func_obj = None

class Curve:

    _token_counter = 0

    @classmethod
    def empty(cls):
        from .empty import Empty
        return Empty()

    @property
    def min_step(self):
        return self._min_step

    @min_step.setter
    def min_step(self, value):
        self._min_step = value

    @property
    def domain(self):
        if self.needs_domain_update:
            self._domain = self.get_domain()
        return self._domain

    @property
    def update_interval(self):
        return self._begin_update_interval

    @property
    def is_updating(self):
        return not self.update_interval.is_empty

    def __init__(self, min_step=None):
        self.name = None
        self._domain = None
        self._observer_data = {}
        self._ordered_observer_tokens = []
        self._begin_update_interval = Interval.empty()
        self._end_update_interval = Interval.empty()
        self.min_step = min_step

    def __call__(self, *args):
        return self.y(args[0])

    def __repr__(self):
        try:
            if bool(self.name):
                return self.name
            return f'{type(self).__name__}("{self.domain}")'
        except Exception as e:
            return super().__repr__() + f'({e})'

    def y(self, x):
        raise Exception("Not implemented")

    def y_start(self):
        return self.y(self.domain.start)

    def y_end(self):
        return self.y(self.domain.end)

    def d_y(self, x, forward=False, min_step=MIN_STEP, limit=None):
        min_step = self.resolve_min_step(min_step)
        if forward:
            x1 = self.x_next(x, min_step=min_step, limit=limit)
        else:
            x1 = self.x_previous(x, min_step=min_step, limit=limit)

        if x1 is None:
            return None
        y1 = self.y(x1)
        if y1 is None:
            return None
        y = self.y(x)
        if y is None:
            return None
        if x1 == x:
            dy = math.inf if y1 >= y else -math.inf
            if not forward:
                dy = -dy
        else:
            dy = (y1 - y) / (x1 - x)
        return dy

    def x(self, y):
        raise Exception("Not implemented")

    def x_next(self, x, min_step=MIN_STEP, limit=None):
        min_step = self.resolve_min_step(min_step)
        if math.isinf(min_step):
            x1 = self.domain.end
        else:
            x1 = x + min_step
        if limit is not None and x1 > limit:
            x1 = limit
        if not self.domain.contains(x1, enforce_start=False):
            return None
        return x1

    def x_previous(self, x, min_step=MIN_STEP, limit=None):
        min_step = self.resolve_min_step(min_step)
        if math.isinf(min_step):
            x1 = self.domain.start
        else:
            x1 = x - min_step
        if limit is not None and x1 < limit:
            x1 = limit
        if not self.domain.contains(x1, enforce_end=False):
            return None
        return x1

    def previous_point(self, x, min_step=MIN_STEP):
        x1 = self.x_previous(x, min_step=min_step)
        if x1 is None:
            return None
        y1 = self.y(x1)
        return (x1, y1)

    def next_point(self, x, min_step=MIN_STEP):
        x1 = self.x_next(x, min_step=min_step)
        if x1 is None:
            return None
        y1 = self.y(x1)
        return (x1, y1)

    def get_domain(self):
        return Interval.empty()

    def resolve_min_step(self, min_step):
        if min_step is None and self.min_step is None:
            return None
        elif min_step is None:
            return self.min_step
        elif self.min_step is None:
            return min_step
        else:
            return max(min_step, self.min_step)

    def sample_points(self, domain=None, min_step=MIN_STEP, step=None):
        min_step = self.resolve_min_step(min_step)
        if domain is None:
            domain = self.domain
        else:
            domain = Interval.intersection([self.domain, domain])
        if domain.is_empty:
            return []
        elif not domain.is_finite:
            raise Exception("Cannot sample points on an infinite domain {}. Specify a finite domain.".format(domain))
        x_start, x_end = domain
        x_end_bin = round(x_end / min_step) if min_step is not None else x_end
        if domain.start_open:
            points = []
        else:
            points = [(x_start, self.y(x_start))]
        if step is not None:
            x = x_start + step
            while x <= x_end:
                y = self.y(x)
                points.append((x, y))
                x += step
        elif min_step is not None and min_step > 0:
            x = self.x_next(x_start, min_step=min_step, limit=x_end)
            while x is not None and x <= x_end:
                y = self.y(x)
                points.append((x, y))
                x_bin = round(x / min_step) if min_step is not None else x
                if x_bin == x_end_bin:
                    break
                x1 = self.x_next(x, min_step=min_step, limit=x_end)
                if x1 is not None:
                    x1_bin = round(x1 / min_step) if min_step is not None else x1
                    if x1_bin <= x_bin:
                        raise Exception('Next x value {} should be greater than the previous x value {} by at least the minimum step of {}'.format(x1, x, min_step))
                x = x1

            if not domain.end_open and points[-1][0] != x_end:
                points.append((x_end, self.y(x_end)))
        else:
            raise Exception("Bad functions sample parameters.")

        return points

    def sample_points_from_x(self, x, limit, backward=False, open=False, min_step=None):
        assert limit is not None
        if limit < 0:
            limit = -limit
            backward = not backward
        min_step = self.resolve_min_step(min_step)
        points = []
        x1 = x
        i = 0

        if not open:
            if x is None:
                return points
            y = self.y(x)
            if y is None:
                return points
            i += 1

        while limit is None or i < limit:
            if not backward:
                x1 = self.x_next(x1, min_step=min_step)
            else:
                x1 = self.x_previous(x1, min_step=min_step)
            if x1 is None:
                break
            y1 = self.y(x1)
            if y1 is None:
                break
            points.append((x1, y1))
            i += 1

        return points

    def get_range(self, domain=None, **kwargs):
        points = self.sample_points(domain=domain, **kwargs)
        low = None
        high = None
        for p in points:
            if low is None or p[1] < low:
                low = p[1]
            if high is None or p[1] > high:
                high = p[1]
        if low is None or high is None:
            return Interval.empty()
        return Interval(low, high)

    def minimise(self, x, min_step=MIN_STEP, step=None, max_iterations=1000):
        x_min = x
        x_min_previous = None
        iterations = 0
        while iterations < max_iterations:
            iterations += 1
            y = self.y(x_min)
            if y is None:
                return x_min_previous
            dy0 = self.d_y(x_min, forward=False)
            dy1 = self.d_y(x_min, forward=True)
            forward = True
            if dy0 is None and dy1 is None:
                return x_min
            elif dy0 is None:
                if dy1 <= 0:
                    forward = True
                else:
                    # Sloping into null value
                    return None
            elif dy1 is None:
                if dy0 >= 0:
                    forward = False
                else:
                    # Sloping into null value
                    return None
            else:
                if dy0 * dy1 < 0 and dy0 <= 0 and dy1 >= 0:
                    # Found minimum
                    return x_min

                if dy0 * dy1 < 0:
                    # Found maximum
                    forward = abs(dy0) < abs(dy1)
                else:
                    # On slope
                    forward = dy1 < 0

            x_min_previous = x_min
            if forward:
                if step is not None:
                    x_min += step
                else:
                    x_min = self.x_next(x_min, min_step=min_step)
            else:
                if step is not None:
                    x_min -= step
                else:
                    x_min = self.x_previous(x_min, min_step=min_step)
        return x_min

    def maximise(self, x, min_step=MIN_STEP, step=None, max_iterations=1000):
        x_max = x
        x_max_previous = None
        iterations = 0
        while iterations < max_iterations:
            iterations += 1
            y = self.y(x_max)
            if y is None:
                return x_max_previous
            dy0 = self.d_y(x_max, forward=False)
            dy1 = self.d_y(x_max, forward=True)
            forward = True
            if dy0 is None and dy1 is None:
                return x_max
            elif dy0 is None:
                if dy1 >= 0:
                    forward = True
                else:
                    # Sloping into null value
                    return None
            elif dy1 is None:
                if dy0 <= 0:
                    forward = False
                else:
                    # Sloping into null value
                    return None
            else:
                if dy0 * dy1 < 0 and dy0 >= 0 and dy1 <= 0:
                    # Found maximum
                    return x_max

                if dy0 * dy1 < 0:
                    # Found minimum
                    forward = abs(dy0) < abs(dy1)
                else:
                    # On slope
                    forward = dy1 > 0

            x_max_previous = x_max
            if forward:
                if step is not None:
                    x_max += step
                else:
                    x_max = self.x_next(x_max, min_step=min_step)
            else:
                if step is not None:
                    x_max -= step
                else:
                    x_max = self.x_previous(x_max, min_step=min_step)
        return x_max

    def regression(self, domain=None, min_step=MIN_STEP, step=None):
        points = self.sample_points(domain=domain, min_step=min_step, step=step)
        for p in points:
            if p[1] is None:
                return None
        count = len(points)
        if count < 2:
            return None
            
        from .line import Line
        if count == 2:
            return Line(p1=points[0], p2=points[1])
        xy = np.vstack(points)
        x = xy[:,0]
        y = xy[:,1]
        A = np.array([x, np.ones(count)])

        # Regression
        w = np.linalg.lstsq(A.T, y, rcond=None)[0]
        m = w[0]
        c = w[1]

        return Line(const=c, slope=m)

    def add_observer(self, *obj, domain=None, begin=None, end=None, autoremove=False, prioritize=False):
        if begin is None and end is None:
            return 0
        
        Curve._token_counter += 1
        token = Curve._token_counter
        domain = Interval.parse(domain, default_inf=True)
        obj_ref = None

        if len(obj) != 0:
            if autoremove:
                # Remove observer automatically
                obj_ref = weakref.ref(obj[0], lambda _: self.remove_observer(token))
            else:
                # Calling remove_observer() is required
                obj_ref = weakref.ref(obj[0])
        elif autoremove:
            raise Exception('Autoremoving an observer requires an object')

        # Do the callback functions require the domain?
        begin_with_interval = False
        end_with_interval = False
        if begin:
            begin_with_interval = util.count_positional_args(begin) == 1
        if end:
            end_with_interval = util.count_positional_args(end) == 1

        # TODO: does saving strong references to callbacks create a retain cycle?
        self._observer_data[token] = (obj_ref, domain, begin, end, begin_with_interval, end_with_interval)
        if prioritize:
            self._ordered_observer_tokens.insert(0, token)
        else:
            self._ordered_observer_tokens.append(token)
        return token

    def remove_observer(self, token_or_obj):
        if isinstance(token_or_obj, Number):
            if token_or_obj in self._observer_data:
                del self._observer_data[token_or_obj]
                self._ordered_observer_tokens.remove(token_or_obj)
        else:
            for token in list(self._ordered_observer_tokens):
                obj_ref = self._observer_data[token][0]
                if obj_ref is not None:
                    obj = obj_ref()
                    if obj is None or obj == token_or_obj:
                        del self._observer_data[token]
                        self._ordered_observer_tokens.remove(token)

    def begin_update(self, domain):
        if domain.is_empty or self._begin_update_interval.is_superset_of(domain):
            return
        self._begin_update_interval = Interval.union([self._begin_update_interval, domain])
        for token in self._ordered_observer_tokens:
            _, callback_interval, callback, _, callback_with_interval, _ = self._observer_data[token]
            if callback_interval is None or domain.intersects(callback_interval):
                if callback is not None:
                    if callback_with_interval:
                        callback(domain)
                    else:
                        callback()

    def end_update(self, domain):
        if domain.is_empty or self._end_update_interval.is_superset_of(domain):
            return
        self._end_update_interval = Interval.union([self._end_update_interval, domain])
        if not self._end_update_interval.is_superset_of(self._begin_update_interval):
            # Keep collecting updates
            return
        
        # Updates complete
        update_interval = self._end_update_interval
        self._begin_update_interval = Interval.empty()
        self._end_update_interval = Interval.empty()
        self.set_needs_interval_update()
        for token in list(self._ordered_observer_tokens):
            _, callback_interval, _, callback, _, callback_with_interval = self._observer_data[token]
            if callback_interval is None or update_interval.intersects(callback_interval):
                if callback is not None:
                    if callback_with_interval:
                        callback(update_interval)
                    else:
                        callback()

    @property
    def needs_domain_update(self):
        return self._domain is None

    def set_needs_interval_update(self):
        self._domain = None

    def map(self, tfm, skip_none=False, name=None, **kwargs):
        from .map import Map
        return Map(self, tfm, skip_none=skip_none, name=name, **kwargs)

    def accumulator_map(self, tfm, degree, is_period=False, interpolation=None, min_step=MIN_STEP, uniform=True):
        from .accumulator_map import AccumulatorMap
        return AccumulatorMap(
            self,
            tfm,
            degree,
            is_period=is_period,
            interpolation=interpolation,
            min_step=min_step,
            uniform=uniform
        )

    def offset(self, x, duration=None):
        from .offset import Offset
        return Offset(self, x, duration=duration)

    def add(self, func):
        return Curve.add_many([self, func])

    def subtract(self, func):
        return Curve.subtract_many([self, func])

    def multiply(self, func):
        return Curve.multiply_many([self, func])

    def divide(self, func):
        return Curve.divide_many([self, func])

    def pow(self, power):
        return type(self).pow_many([self, power])

    def raised(self, base):
        return type(self).pow_many([base, self])

    def log(self, base=math.e):
        return type(self).log_many([self, base])

    def integral(self, const=0, interpolation=None, uniform=True):
        from .integral import Integral

        return Integral(self, const=const, interpolation=interpolation, uniform=uniform)

    def additive_inverse(self):
        return self.map(_additive_inverse)

    def multiplicative_inverse(self):
        return self.map(_multiplicative_inverse)

    def abs(self):
        return self.map(_abs)

    def blend(self, func, x_blend_start, x_blend_stop):
        from .aggregate import Aggregate
        from .piecewise import Piecewise
        
        x_blend_period = x_blend_stop - x_blend_start
        def blend_f(x, ys):
            u = (x - x_blend_start) / x_blend_period
            return (1.0 - u) * ys[0] + u * ys[1]
        c = Aggregate([self, func], tfm=blend_f, name='blend')

        funcs = [self, c, func]
        domains = self.domain.partition([x_blend_start, x_blend_stop])
        return Piecewise(funcs, domains)

    def extension(self, name, start=False, end=True, raise_on_empty=False, **kwds):
        from .extension import ConstantExtension
        from .extension import TangentExtension
        from .extension import SinExtension
        from .extension import HarmonicExtension
        from .extension import WeaveExtension

        classes = [            
            ConstantExtension,
            TangentExtension,
            SinExtension,
            HarmonicExtension,
            WeaveExtension
        ]

        for c in classes:
            if c.name == name:
                return c(self, start=start, end=end, raise_on_empty=raise_on_empty, **kwds)
        
        raise Exception('Unknown extension type')

    # def wave_extended(self, ref_func, min_deviation=0, start=None, step=None, min_step=MIN_STEP):
    #     if self.domain.is_positive_infinite:
    #         return self
    #     ref_func = Curve.parse(ref_func)
    #     extremas = Extremas(self, ref_func, min_deviation=min_deviation, start=start, step=step, min_step=min_step)

    # def mom(self, degree, duration, **kwargs):
    #     """
    #     Returns the momentum of the reciever.

    #     The degree corresponds to the number of steps to take.
    #     """
    #     degree = int(degree)
    #     if degree < 1:
    #         raise ValueError(f'Momentum requires a positive degree, got: {degree}')
    #     from pyduration import Duration
    #     duration = Duration.parse(duration)
    #     def _mom(x, y):
    #         if y is None:
    #             return None
    #         # step back
    #         x0 = duration.step(x, -degree)
    #         y0 = self.y(x0)
    #         if y0 is None:
    #             return None
    #         return y - y0
    #     return self.map(_mom, name=f'mom({degree})', **kwargs)

    def sma(self, degree, is_period=False, **kwargs):
        from .sma import SMA
        return SMA(self, degree, is_period=is_period, **kwargs)

    def ema(self, degree, is_period=False, init=None, **kwargs):
        from .ema import EMA
        return EMA(self, degree, is_period=is_period, init=init, **kwargs)

    def smma(self, degree, **kwargs):
        from .sma import SMA
        from .ema import EMA
        sma = SMA(self, degree, is_period=False, **kwargs)
        ema = EMA(self, 1 / degree, is_period=False, init=sma, **kwargs)
        return ema

    def harmonic_smas(self, base_degree, count, stride=1, is_period=False, **kwargs):
        """
        Returns `count` SMAs from small to large. Their degrees
        are proportional to the golden ratio.
        """
        periods = []
        smas = []
        step = stride + 1

        for i in range(count):
            period = base_degree * GOLD ** float(i * step)
            period = round(period / base_degree) * base_degree
            periods.append(period)

        for i in range(count):
            period = periods[i]
            sma = self.sma(period, is_period=is_period, **kwargs)
            smas.append(sma)

        return smas

    def centered_macs(self, base_degree, count, stride=1, is_period=False, **kwargs):
        periods = []
        smas = []
        step = stride + 1

        for i in range(count):
            period = base_degree * GOLD ** float(i * step)
            period = round(period / base_degree) * base_degree
            periods.insert(0, period)

        for i in range(count):
            period = periods[i]
            sma = self.sma(period, is_period=is_period, **kwargs)
            smas.append(sma)

        return smas

    def rsi(self, degree, **kwargs):
        d = self.differential()
        du = Curve.max([d, 0], ignore_empty=False)
        dd = Curve.max([-d, 0], ignore_empty=False)
        rs = du.ema(1 / degree, **kwargs) / dd.ema(1 / degree, **kwargs)
        rsi = 100 - 100 / (1 + rs)
        rsi.name = f'rsi({degree})'
        return rsi

    def trailing_min(self, degree, is_period=False, interpolation=None, min_step=MIN_STEP, uniform=True):
        return self.accumulator_map(
            min,
            degree,
            is_period=is_period,
            interpolation=interpolation,
            min_step=min_step,
            uniform=uniform
        )

    def trailing_max(self, degree, is_period=False, interpolation=None, min_step=MIN_STEP, uniform=True):
        return self.accumulator_map(
            max,
            degree,
            is_period=is_period,
            interpolation=interpolation,
            min_step=min_step,
            uniform=uniform
        )

    def differential(self, forward=False):
        from .map import Map
        d = Map(self, lambda x, y: self.d_y(x, forward=forward))
        d.name = 'diff'
        return d

    def subset(self, domain):
        from .generic import Generic
        return Generic(self, domain=domain, min_step=self.min_step)

    @classmethod
    def first(cls, funcs, *args):
        """
        Return a func which returns the first value which is not `None`.
        """
        if not isinstance(funcs, Sequence):
            funcs = [funcs] + list(args)
        from .aggregate import Aggregate

        def first_val(x, vals):
            for v in vals:
                if v is not None:
                    return v
            return None

        funcs = Curve.parse_many(funcs)
        return Aggregate(funcs, tfm=first_val, union=True, name='first')        

    @classmethod
    def min(cls, funcs, *args, ignore_empty=False):
        if not isinstance(funcs, Sequence):
            funcs = [funcs] + list(args)
        from .aggregate import Aggregate

        def min_vals(x, vals):
            best = None
            for val in vals:
                if best is None or (val is not None and val < best):
                    best = val
            return best

        def min_vals_with_empty(x, vals):
            return min(filter(lambda y: y is not None, vals), default=None)

        funcs = Curve.parse_many(funcs)
        t = min_vals_with_empty if ignore_empty else min_vals
        return Aggregate(funcs, tfm=t, union=ignore_empty, name='min')

    @classmethod
    def max(cls, funcs, *args, ignore_empty=False):
        if not isinstance(funcs, Sequence):
            funcs = [funcs] + list(args)
        from .aggregate import Aggregate

        def max_vals(x, vals):
            best = None
            for val in vals:
                if best is None or (val is not None and val > best):
                    best = val
            return best

        def max_vals_with_empty(x, vals):
            return max(filter(lambda y: y is not None, vals), default=None)

        funcs = Curve.parse_many(funcs)
        t = max_vals_with_empty if ignore_empty else max_vals
        return Aggregate(funcs, tfm=t, union=ignore_empty, name='max')

    @classmethod
    def add_many(cls, funcs, *args):
        if not isinstance(funcs, Sequence):
            funcs = [funcs] + list(args)
        from .aggregate import Aggregate

        def add_f(x, ys):
            for y in ys:
                if y is None:
                    return None
            return sum(ys)
        return Aggregate(funcs, tfm=add_f, name='add', operator='+')

    @classmethod
    def subtract_many(cls, funcs, *args):
        if not isinstance(funcs, Sequence):
            funcs = [funcs] + list(args)
        from .aggregate import Aggregate

        def sub_f(x, ys):
            result = 0
            for i, y in enumerate(ys):
                if y is None:
                    return None
                if i == 0:
                    result = y
                else:
                    result -= y
            return result
        return Aggregate(funcs, tfm=sub_f, name='sub', operator='-')

    @classmethod
    def multiply_many(cls, funcs, *args):
        if not isinstance(funcs, Sequence):
            funcs = [funcs] + list(args)
        from .aggregate import Aggregate

        def mult_f(x, ys):
            geo_sum = 1.0
            for y in ys:
                if y is None:
                    return None
                geo_sum *= y
            return geo_sum
        return Aggregate(funcs, tfm=mult_f, name='mult', operator='*')

    @classmethod
    def divide_many(cls, funcs, *args):
        if not isinstance(funcs, Sequence):
            funcs = [funcs] + list(args)
        from .aggregate import Aggregate

        def div_f(x, ys):
            result = 0
            for i, y in enumerate(ys):
                if y is None:
                    return None
                if i == 0:
                    result = y
                elif y == 0:
                    result = math.inf if result >= 0 else -math.inf
                else:
                    result /= y
            return result
        return Aggregate(funcs, tfm=div_f, name='div', operator='/')

    @classmethod
    def pow_many(cls, funcs, *args):
        if not isinstance(funcs, Sequence):
            funcs = [funcs] + list(args)
        from .aggregate import Aggregate

        def log_f(x, ys):
            result = 0
            for i, y in enumerate(ys):
                if y is None:
                    return None
                if i == 0:
                    result = y
                else:
                    result = result ** y
            return result
        return Aggregate(funcs, tfm=log_f, name='pow', operator='^')

    @classmethod
    def log_many(cls, funcs, *args):
        if not isinstance(funcs, Sequence):
            funcs = [funcs] + list(args)
        from .aggregate import Aggregate

        def log_f(x, ys):
            result = 0
            for i, y in enumerate(ys):
                if y is None:
                    return None
                if i == 0:
                    result = y
                else:
                    result = math.log(result, y)
            return result
        return Aggregate(funcs, tfm=log_f, name='log')

    @classmethod
    def zero(cls, value):
        from .constant import Constant
        return Constant.zero()

    @classmethod
    def const(cls, value):
        from .constant import Constant
        return Constant(value)

    @classmethod
    def parse(cls, func):
        from .generic import Generic
        from .constant import Constant
        from .points import Points

        if func is None:
            return None
        elif isinstance(func, Curve):
            return func
        elif callable(func):
            return Generic(func)
        elif isinstance(func, Number):
            return Constant(func)
        elif isinstance(func, Sequence):
            # Parse points
            if len(func) == 0:
                return Points(func)
            else:
                if isinstance(func[0], Sequence):
                    if len(func[0]) == 2:
                        return Points(func)
        elif isinstance(func, Mapping):
            return cls.parse_descriptor(func)
        raise Exception('Unable to parse function')

    @classmethod
    def parse_descriptor(cls, d, fragment=False, current_func=None, decorators=None):
        # Example:
        # {
        #     "$line": {
        #         "points": [
        #             ["2020-02-12 01:23+1200", 8765.56],
        #             ["2020-02-30 04:50+1200", 6765.56]
        #         ]
        #     }
        # }
        if decorators is None:
            decorators = []

        def next_func_constructor(fname):
            f = current_func or _func_obj
            assert isinstance(f, Curve)
            ftype = type(f)
            fconstructor = None
            fconstructor_from_instance = False
            type_method_names = list(map(lambda x: x[0], inspect.getmembers(ftype, predicate=inspect.ismethod)))
            f_method_names = list(map(lambda x: x[0], inspect.getmembers(f, predicate=inspect.ismethod)))
            if f'{fname}_many' in type_method_names:
                fname = f'{fname}_many'
            if fname in type_method_names:
                def _create_class_fconstructor(fname):
                    def _class_fconstructor(*args, **kwargs):
                        f = current_func or _func_obj
                        fmethod = getattr(type(f), fname)
                        return fmethod(*args, **kwargs)
                    return _class_fconstructor
                fconstructor = _create_class_fconstructor(fname)
                fconstructor_from_instance = False
            elif fname in f_method_names:
                def _create_fconstructor(fname):
                    def _fconstructor(*args, **kwargs):
                        f = current_func or _func_obj
                        fmethod = getattr(f, fname)
                        return fmethod(*args, **kwargs)
                    return _fconstructor
                fconstructor = _create_fconstructor(fname)
                fconstructor_from_instance = True
            else:
                raise ValueError(f'Bad function name: {fname}')
            return fconstructor, fconstructor_from_instance
        
        if isinstance(d, Mapping):
            fragment_vals = {}

            for k, v in d.items():

                if k.startswith('@'):
                    # This is an decorator descriptor
                    oname = k[1:]
                    decorator_i = len(decorators)
                    decorators.insert(decorator_i, oname)
                    v = cls.parse_descriptor(v,
                        fragment=fragment,
                        current_func=current_func,
                        decorators=decorators
                    )
                    del decorators[decorator_i]

                    if oname.startswith('log'):
                        # Log space has ended, exit log space
                        # by raising to power
                        base_str = oname[3:]
                        base = int(base_str) if bool(base_str) else math.e
                        v = base ** v
                    
                    if isinstance(v, Curve):
                        # Allow chaining
                        current_func = v
                        continue
                    if oname != 'args':
                        # Only let @args pass through to parent
                        if len(d) != 1:
                            raise ValueError(f'A decorator (@...) can only have siblings in a fragment')
                        return v

                elif k.startswith('$'):
                    # This is function descriptor
                    fname = k[1:]

                    fconstructor = None
                    fconstructor_from_instance = False

                    if fname == 'const' or fname == 'constant':
                        from .constant import Constant
                        fconstructor = Constant
                    elif fname == 'line':
                        from .line import Line
                        fconstructor = Line
                    elif fname.startswith('log'):
                        base_str = fname[3:]
                        base = int(base_str) if bool(base_str) else math.e
                        def _dot_log(*args, **kwargs):
                            return current_func.log(**util.extend({ "base": base }, kwargs))
                        fconstructor = _dot_log
                        fconstructor_from_instance = True
                    else:
                        fconstructor, fconstructor_from_instance = next_func_constructor(fname)

                    func_args = cls.parse_descriptor(v,
                        fragment=True,
                        decorators=decorators
                    )
                    args = []
                    kwargs = {}
                    if isinstance(func_args, dict):
                        kwargs = func_args
                    elif isinstance(func_args, list):
                        args = func_args
                    else:
                        args = [func_args]
                    
                    # Check for nested args
                    if '@args' in kwargs:
                        args = kwargs['@args']
                        del kwargs['@args']

                    if fconstructor_from_instance and current_func is None:
                        current_func = Curve.parse(args[0])
                        del args[0]
                    elif not fconstructor_from_instance and current_func is not None:
                        # Add current function as first argument or to
                        # list at first argument
                        if bool(args) and isinstance(args[0], list):
                            args[0][0:0] = [current_func]
                        else:
                            args[0:0] = [current_func]
                    current_func = fconstructor(*args, **kwargs)
                    continue

                if current_func is not None:
                    raise Exception(f'Unexpected key after a function: {k}')

                if isinstance(v, Mapping):
                    fragment_vals[k] = cls.parse_descriptor(v,
                        fragment=True,
                        decorators=decorators
                    )
                elif isinstance(v, Sequence) and not isinstance(v, (str, bytes)):
                    fragment_vals[k] = cls.parse_descriptor(v,
                        fragment=True,
                        decorators=decorators
                    )
                else:
                    fragment_vals[k] = v
            
            return current_func or fragment_vals
        elif fragment:
            if isinstance(d, Mapping):
                return {k: cls.parse_descriptor(v,
                    fragment=True,
                    decorators=decorators
                ) for k, v in d.items()}
            elif isinstance(d, Sequence) and not isinstance(d, (str, bytes)):
                return [cls.parse_descriptor(v,
                    fragment=True,
                    decorators=decorators
                ) for v in d]
            elif 'date' in decorators:
                return arrow.get(d).timestamp
            elif isinstance(d, Number):
                if 'log' in decorators:
                    return math.log(d)
                elif 'log2' in decorators:
                    return math.log(d, 2)
                elif 'log10' in decorators:
                    return math.log(d, 10)
                else:
                    return d
            else:
                return d
        else:
            raise TypeError('Unexpected type found while parsing a function')

    @classmethod
    def parse_many(cls, funcs, *args):
        if not isinstance(funcs, Sequence):
            funcs = [funcs] + list(args)
        return list(map(cls.parse, funcs))

    @classmethod
    def count_positional_args(cls, f, default=1):
        if not callable(f):
            raise Exception('Expected callable function')
        if inspect.isbuiltin(f):
            return default
        sig = inspect.signature(f)
        count = 0
        for param in sig.parameters.values():
            if param.kind == inspect.Parameter.POSITIONAL_ONLY or \
                param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD:
                count += 1
        return count

    def __add__(self, other):
        return Curve.add_many([self, other])

    def __sub__(self, other):
        return Curve.subtract_many([self, other])

    def __mul__(self, other):
        return Curve.multiply_many([self, other])

    def __truediv__(self, other):
        return Curve.divide_many([self, other])

    def __pow__(self, other):
        return Curve.pow_many([self, other])

    def __radd__(self, other):
        return Curve.add_many([other, self])

    def __rsub__(self, other):
        return Curve.subtract_many([other, self])

    def __rmul__(self, other):
        return Curve.multiply_many([other, self])

    def __rtruediv__(self, other):
        return Curve.divide_many([other, self])

    def __rpow__(self, other):
        return Curve.pow_many([other, self])

    def __neg__(self):
        return self.additive_inverse()

    def __pos__(self):
        return self

    def __abs__(self):
        return self.abs()

def _additive_inverse(x, y):
    if y is None:
        return None
    return -y

def _multiplicative_inverse(x, y):
    if y is None:
        return None
    return 1 / y

def _abs(x, y):
    if y is None:
        return None
    return abs(y)

def _callable_arg_len(f, vararg_ret_val):
    args, varargs, _, _ = inspect.getargspec(f)
    if varargs is not None:
        return vararg_ret_val
    arg_len = len(args)
    if arg_len == 0:
        return 0
    if args[0] == 'self':
        arg_len -= 1
    return arg_len

_func_obj = Curve()
