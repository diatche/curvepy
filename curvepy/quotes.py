from .curve import Curve, MIN_STEP
from .map import Map
from .points import Points
from intervalpy import Interval
from pyduration import Duration

OHLC_KEYS = ['open', 'high', 'low', 'close', 'volume']
OHLC_POINT_COUNT = len(OHLC_KEYS)
OHLC_STEPS = OHLC_POINT_COUNT - 1
QUOTE_MIN_STEP_COEFFICIENT = 0.1

OPEN = 0
HIGH = 1
LOW = 2
CLOSE = 3
VOLUME = 4


class Quotes(Curve):
    """
    Represents quotes as [open, high, low, close, (volume)].
    """

    @property
    def close(self):
        if self._close is None:
            self._close = Map(
                self,
                lambda q: q[CLOSE],
                skip_none=True,
                name='close'
            )
        return self._close

    @property
    def open(self):
        if self._open is None:
            self._open = Map(
                self,
                lambda q: q[OPEN],
                skip_none=True,
                name='open'
            )
        return self._open

    @property
    def high(self):
        if self._high is None:
            self._high = Map(
                self,
                lambda q: q[HIGH],
                skip_none=True,
                name='high'
            )
        return self._high

    @property
    def low(self):
        if self._low is None:
            self._low = Map(
                self,
                lambda q: q[LOW],
                skip_none=True,
                name='low'
            )
        return self._low

    @property
    def hl2(self):
        if self._hl2 is None:
            self._hl2 = Map(
                self,
                lambda q: (q[HIGH] + q[LOW]) / 2,
                skip_none=True,
                name='hl2'
            )
        return self._hl2

    @property
    def volume(self):
        if self._volume is None:
            self._volume = Map(
                self,
                lambda q: q[VOLUME],
                skip_none=True,
                name='volume'
            )
        return self._volume

    def get_domain(self):
        return self._quote_points.domain
        # if domain.is_empty:
        #     return domain
        # return self.duration.span(domain, start_open=False)

    def __init__(self, duration, quote_points=None, **kwargs):
        """
        `quote_points` are assumed to be in the form [timestamp, [o, h, l, c, v]]
        in strict ascending order with no gaps and with the same duration as the receiver.
        """
        duration = Duration.parse(duration)
        self.duration = duration
        super().__init__(min_step=duration.min_seconds * 0.01, **kwargs)
        self._quote_points = Points(
            [], interpolation=Points.interpolation.previous, uniform=duration.is_uniform)
        self._quote_points.add_observer(begin=self.begin_update, end=self.end_update, prioritize=True)
        self._close = None
        self._open = None
        self._high = None
        self._low = None
        self._hl2 = None
        self._ohlc = None
        self._volume = None
        if quote_points is not None:
            self.set(quote_points)

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

    def append(self, quote_point):
        """
        `quote_points` are assumed to be in the form [timestamp, [o, h, l, c, v]]
        in strict ascending order with no gaps and with the same duration as the receiver.
        """
        self.append_list([quote_point])

    def append_list(self, quote_points):
        """
        `quote_points` are assumed to be in the form [timestamp, [o, h, l, c, v]]
        in strict ascending order with no gaps and with the same duration as the receiver.
        """
        if self.domain.is_empty:
            return self.set(quote_points)
        self._quote_points.append_list(quote_points)

    def set(self, quote_points):
        """
        `quote_points` are assumed to be in the form [timestamp, [o, h, l, c, v]]
        in strict ascending order with no gaps and with the same duration as the receiver.
        """
        self._quote_points.set(quote_points)

    def sample(self, domain=None, min_step=MIN_STEP, step=None):
        points = self.sample_points(
            domain=domain,
            min_step=min_step,
            step=step
        )
        return [p[1] for p in points]

    def sample_points(self, domain=None, min_step=MIN_STEP, step=None):
        domain = Interval.parse(domain, default_inf=True)
        if domain.is_empty:
            return []
        pinterval = self.duration.span(domain, start_open=False)
        return self._quote_points.sample_points(domain=pinterval, min_step=min_step, step=step)

    def y(self, x):
        return self._quote_points.y(x)

    def x_next(self, x, min_step=MIN_STEP, limit=None):
        # return self.duration.next(x)
        return self._quote_points.x_next(x, min_step=min_step, limit=limit)

    def x_previous(self, x, min_step=MIN_STEP, limit=None):
        # return self.duration.previous(x)
        return self._quote_points.x_previous(x, min_step=min_step, limit=limit)
