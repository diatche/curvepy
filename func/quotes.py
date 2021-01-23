import math
from .func import Func, MIN_STEP
from .map import Map
from .points import Points
from intervalpy import Interval
from pyduration import Duration

OHLC_POINT_COUNT = 4
OHLC_STEPS = OHLC_POINT_COUNT - 1
QUOTE_MIN_STEP_COEFFICIENT = 0.1


class Quotes(Func):
    """
    Represents quotes as [open, high, low, close, (volume)].
    """

    @property
    def close(self):
        if self._close is None:
            self._close = Map(
                self,
                lambda q: q.close,
                skip_none=True,
                name='close'
            )
        return self._close

    @property
    def high(self):
        if self._high is None:
            self._high = Map(
                self,
                lambda q: q.high,
                skip_none=True,
                name='high'
            )
        return self._high

    @property
    def low(self):
        if self._low is None:
            self._low = Map(
                self,
                lambda q: q.low,
                skip_none=True,
                name='low'
            )
        return self._low

    @property
    def hl2(self):
        if self._hl2 is None:
            self._hl2 = Map(
                self,
                lambda q: (q.high + q.low) / 2,
                skip_none=True,
                name='hl2'
            )
        return self._hl2

    @property
    def ohlc(self):
        if self._ohlc is None:
            self._ohlc = OHLC(self)
        return self._ohlc

    @property
    def volume(self):
        if self._volume is None:
            self._volume = Map(
                self,
                lambda q: q.volume,
                skip_none=True,
                name='volume'
            )
        return self._volume

    def get_domain(self):
        return self._quote_points.domain

    def __init__(self, duration, quotes=None, **kwargs):
        """
        `quotes` are assumed to be instances of quotes, strictly ordered in ascending order and spaced at equal intervals.
        """
        duration = Duration.parse(duration)
        self.duration = duration
        super().__init__(min_step=duration.min_seconds * 0.01, **kwargs)
        self._quote_points = Points(
            [], interpolation=Points.interpolation.previous, uniform=duration.is_uniform)
        self._quote_points.add_observer(begin=self.begin_update, end=self.end_update, prioritize=True)
        self._close = None
        self._high = None
        self._low = None
        self._hl2 = None
        self._ohlc = None
        self._volume = None
        if quotes is not None:
            self.set(quotes)

    def __repr__(self):
        try:
            return f'quotes({self.duration})'
        except Exception as e:
            return super().__repr__() + f'({e})'

    def last_quote(self):
        return self.y_end()

    def first_quote(self):
        return self.y_start()

    def get_range(self, domain=None, **kwargs):
        quotes = self.sample(domain=domain, **kwargs)
        low = None
        high = None
        for q in quotes:
            if low is None or q.low < low:
                low = q.low
            if high is None or q.high > high:
                high = q.high
        if low is None or high is None:
            return Interval.empty()
        return Interval(low, high)

    def ao(self):
        """
        The Awesome Oscillator is an indicator used to measure market momentum.
        AO calculates the difference of a 34 Period and 5 Period Simple Moving Averages.
        The Simple Moving Averages that are used are not calculated using closing
        price but rather each bar's midpoints. AO is generally used to affirm trends
        or to anticipate possible reversals.
        """
        uniform = self.duration.is_uniform
        return self.hl2.sma(5, uniform=uniform) - self.hl2.sma(34, uniform=uniform)

    def alligator(self):
        """
        The Alligator indicator uses three smoothed moving averages, set at five,
        eight and 13 periods, which are all Fibonacci numbers. The initial smoothed
        average is calculated with a simple moving average (SMA), adding additional
        smoothed averages that slow down indicator turns.
        """
        uniform = self.duration.is_uniform
        jaw = self.hl2.sma(13, uniform=uniform).offset(8, duration=self.duration)
        teeth = self.hl2.sma(8, uniform=uniform).offset(5, duration=self.duration)
        lips = self.hl2.sma(5, uniform=uniform).offset(3, duration=self.duration)
        return jaw, teeth, lips

    def trailing_high(self, degree, is_period=False):
        return self.high.trailing_max(degree, is_period=is_period, interpolation=-1, uniform=self.duration.is_uniform)

    def trailing_low(self, degree, is_period=False):
        return self.low.trailing_max(degree, is_period=is_period, interpolation=-1, uniform=self.duration.is_uniform)

    def append(self, quote):
        """
        Quotes are assumed to be instances of quotes in strict ascending order
        with no gaps and with the same duration as the receiver.
        """
        self.append_list([quote])

    def append_list(self, quotes):
        """
        Quotes are assumed to be instances of quotes in strict ascending order
        with no gaps and with the same duration as the receiver.
        """
        if self.domain.is_empty:
            return self.set(quotes)
        self._quote_points.append_list([(q.date, q) for q in quotes])

    def set(self, quotes):
        """
        `quotes` are assumed to be instances of quotes in strict ascending order
        with no gaps and with the same duration as the receiver.
        """
        quote_points = [(q.date, q) for q in quotes]
        self._quote_points.set(quote_points)

    def sample(self, domain=None, min_step=MIN_STEP, step=None):
        domain = Interval.parse(domain, default_inf=True)
        pinterval = self.duration.pad(domain, start=1, end=1, start_open=False)
        points = self.sample_points(
            domain=pinterval,
            min_step=min_step,
            step=step
        )
        return [p[1] for p in points]

    def sample_points(self, domain=None, min_step=MIN_STEP, step=None):
        return self._quote_points.sample_points(domain=domain, min_step=min_step, step=step)

    def y(self, x):
        return self._quote_points.y(x)

    def x_next(self, x, min_step=MIN_STEP, limit=None):
        return self._quote_points.x_next(x, min_step=min_step, limit=limit)

    def x_previous(self, x, min_step=MIN_STEP, limit=None):
        return self._quote_points.x_previous(x, min_step=min_step, limit=limit)


class OHLC(Map):

    def get_domain(self):
        quote_func: Quotes = self.func
        domain = quote_func.domain
        if domain.is_point:
            domain = quote_func.duration.span(domain, start_open=False)
        else:
            domain = quote_func.duration.pad(domain.as_open(), end=1, start_open=True)
        return domain.as_closed()

    def __init__(self, quote_func):
        super().__init__(quote_func, self.quote_map)

    def __repr__(self):
        try:
            return f'{self.func}.ohlc'
        except Exception as e:
            return super().__repr__() + f'({e})'

    def quote_map(self, x, quote):
        if not self.domain.contains(x):
            return None
        if self.domain.is_empty:
            return None
        if quote is None:
            quote = self.func.last_quote()
        if x <= quote.domain.start:
            return quote.open
        elif x >= quote.domain.end:
            return quote.close
        else:
            points = quote.ohlc_points
            uq = (x - quote.start_date) / quote.domain.length
            i_ = uq * OHLC_STEPS
            up = i_ % 1.0
            i = int(i_)
            return (1.0 - up) * points[i][1] + up * points[i + 1][1]

    def x_next(self, x, min_step=MIN_STEP, limit=None):
        if not self.domain.contains(x + min_step, enforce_start=False):
            return None
        qi_ = self.func._quote_points.x_index(x + min_step)
        if qi_ is None:
            return None
        q = self.func.y(x)
        if q is None:
            if x > self.func.domain.end:
                q = self.func.last_quote()
            else:
                return self.domain.start
        uq = (x + min_step - q.start_date) / q.domain.length
        i_ = uq * OHLC_STEPS
        u = max(0, math.ceil(i_)) / OHLC_STEPS
        return q.start_date + u * q.domain.length

    def x_previous(self, x, min_step=MIN_STEP, limit=None):
        if not self.domain.contains(x - min_step, enforce_end=False):
            return None
        qi_ = self.func._quote_points.x_index(x + min_step)
        if qi_ is None:
            return None
        q = self.func.y(x)
        if q is None:
            if x > self.func.domain.end:
                q = self.func.last_quote()
            else:
                return self.domain.end
        uq = (x - min_step - q.start_date) / q.domain.length
        i_ = uq * OHLC_STEPS
        u = min(OHLC_POINT_COUNT - 1, math.floor(i_)) / OHLC_STEPS
        return q.start_date + u * q.domain.length

