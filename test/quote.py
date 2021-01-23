import datetime
import arrow
from typing import *
from numbers import Number
from time import time
from intervalpy import Interval
from pyduration import Duration
from . import test_util
from collections.abc import Mapping

DAY = 86400
HOUR = 3600
MINUTE = 60

OHLC_KEYS = ['open', 'high', 'low', 'close']
DOMAIN_START_OPEN = False


class Quote:

    def __init__(self, *ohlc, date=None, volume=None, resolution=None, res=None):
        ohlc = test_util.flatten(ohlc)
        assert len(ohlc) >= 4
        if volume is None and len(ohlc) > 4:
            volume = float(ohlc[4])

        resolution = resolution or res
        assert date >= 0
        assert volume >= 0
        assert resolution is not None
        super().__init__()
        self._start_date = date
        self._resolution = Duration.parse(resolution)
        self.open = float(ohlc[0])
        self.high = float(ohlc[1])
        self.low = float(ohlc[2])
        self.close = float(ohlc[3])
        assert self.open > 0
        assert self.high > 0
        assert self.low > 0
        assert self.close > 0
        self.volume = volume
        self._price_domain = None

        self.reset_transient_time()

    def __repr__(self):
        try:
            vals = list(self.ohlc)
            if self.date is not None:
                vals.append(test_util.date(self.date))
            return f'({", ".join(map(str, vals))})'
        except Exception as e:
            return super().__repr__() + f'({e})'

    def get_values(self):
        return {
            'open': self.open,
            'high': self.high,
            'low': self.low,
            'close': self.close,
            'date': self.date,
            'volume': self.volume,
            'res': self.resolution,
        }

    @property
    def middle(self):
        return (self.high + self.low) / 2

    @property
    def is_final(self):
        return self.end_date <= time()

    @property
    def price(self):
        return self.close

    @property
    def ohlc(self):
        return (self.open, self.high, self.low, self.close)

    @property
    def ohlcv(self):
        return (self.open, self.high, self.low, self.close, self.volume)

    @property
    def ohlcv_point(self):
        return (self.date, (self.open, self.high, self.low, self.close, self.volume))

    @classmethod
    def to_ohlcv(cls, quotes: Iterable):
        return [q.ohlcv for q in quotes]

    @classmethod
    def to_ohlcv_points(cls, quotes: Iterable):
        return [q.ohlcv_point for q in quotes]

    @property
    def close_point(self):
        if self.date is None:
            return None
        return (self.date, self.close)

    @property
    def date(self):
        return self._start_date

    @property
    def start_date(self):
        return self._start_date

    @property
    def end_date(self):
        if self._end_date is None:
            self._end_date = self.resolution.next(self.start_date)
        return self._end_date

    @property
    def domain(self):
        if self._domain is None:
            self._domain = Interval(
                self.start_date,
                self.end_date,
                start_open=DOMAIN_START_OPEN,
                end_open=not DOMAIN_START_OPEN
            )
        return self._domain

    @property
    def price_domain(self):
        if self._price_domain is None:
            self._price_domain = Interval.closed(self.low, self.high)
        return self._price_domain

    @property
    def resolution(self):
        return self._resolution

    @resolution.setter
    def resolution(self, value):
        self._resolution = value
        self.reset_transient_time()

    @property
    def average_price(self):
        """
        A larger shadow often means that there was more volume
        towards that side of the candle.
        """
        o = self.open
        h = self.high
        l = self.low
        c = self.close
        upper_shadow = h - max(o, c)
        lower_shadow = min(o, c) - l
        shadow_sum = upper_shadow + lower_shadow
        if shadow_sum == 0:
            return c
        return (h * upper_shadow + l * lower_shadow) / shadow_sum
        # extrema_weight = GOLD - 1.0
        # extrema = self.high
        # if upper_shadow < lower_shadow:
        #     extrema = self.low
        # return extrema_weight * extrema + (1.0 - extrema_weight) * self.close

    @property
    def is_empty(self):
        return self.volume == 0

    def reset_transient_time(self):
        self._end_date = None
        self._domain = None

    def equals(self, other):
        return type(self) == type(other) and \
            self.date == other.date and \
            self.resolution == other.resolution and \
            self.open == other.open and \
            self.high == other.high and \
            self.low == other.low and \
            self.close == other.close and \
            self.volume == other.volume

    def __eq__(self, other):
        return self.equals(other)

    def __ne__(self, other):
        return not self.equals(other)

    @staticmethod
    def is_contiguous(quotes):
        return Quote.missing_interval_count(quotes) == 0

    @classmethod
    def missing_interval_count(cls, quotes):
        quotes_len = len(quotes)
        if quotes_len == 0:
            return 0

        quote_domain = cls.list_domain(quotes)
        expected_count = quotes[0].resolution.count(quote_domain, start_open=quote_domain.start_open)
        return expected_count - len(quotes)

    @classmethod
    def missing_domains(cls, quotes, domain=None):
        # TODO: optimise by recursively dividing quotes
        # in half and checking if the quotes are
        # contiguous. Then collect domains between
        # contiguous quotes.
        quotes_len = len(quotes)
        if quotes_len == 0:
            if domain is None:
                return []
            else:
                return [domain]

        if domain is None:
            domain = cls.list_domain(quotes)
        else:
            domain = Interval.parse(domain)
        if domain.is_empty:
            return []

        missing_list = []
        head = Interval.intersection(
            [domain, quotes[0].domain.rest_to_negative_infinity()])
        if not head.is_empty:
            missing_list.append(head)

        for i in range(1, quotes_len):
            q0 = quotes[i - 1]
            q1 = quotes[i]
            if q0.end_date != q1.start_date:
                if q0.end_date > q1.start_date:
                    continue
                missing = Interval(
                    q0.domain.end,
                    q1.domain.start,
                    start_open=not q0.domain.end_open,
                    end_open=not q1.domain.start_open)
                missing_list.append(missing)

        tail = Interval.intersection(
            [domain, quotes[-1].domain.rest_to_positive_infinity()])
        if not tail.is_empty:
            missing_list.append(tail)

        return missing_list

    @classmethod
    def aggregate_single(cls, quotes, resolution=None) -> 'Quote':
        if len(quotes) == 0:
            raise Exception('Cannot aggregate quote from empty list')
            
        o = quotes[0].open
        c = quotes[-1].close
        l = o
        h = o
        v = 0
        for q in quotes:
            if q.low < l:
                l = q.low
            if q.high > h:
                h = q.high
            v += q.volume
        if resolution is not None:
            resolution = Duration.parse(resolution)
        else:
            resolution = quotes[0].resolution.aggregate(len(quotes))
        date = resolution.floor(quotes[0].date)
        return Quote(o, h, l, c, date=date, volume=v, resolution=resolution)

    @classmethod
    def aggregate(cls, quotes, resolution=None) -> List['Quote']:
        if len(quotes) == 0:
            return []

        resolution = Duration.parse(resolution)
        if resolution == quotes[0].resolution:
            # No aggregation necessary
            return quotes
        elif resolution < quotes[0].resolution:
            raise Exception('Aggregate resolution is smaller than the quote resolution')
        agr_quotes: List[Quote] = []
        current_start_date = None
        span_quotes = []
        for quote in quotes:
            start_date = resolution.floor(quote.date)
            if start_date != current_start_date:
                if len(span_quotes) != 0:
                    agr_quote = cls.aggregate_single(span_quotes, resolution=resolution)
                    agr_quotes.append(agr_quote)
                    span_quotes.clear()
                current_start_date = start_date
            if start_date == current_start_date:
                span_quotes.append(quote)
        if len(span_quotes) != 0:
            agr_quote = cls.aggregate_single(span_quotes, resolution=resolution)
            agr_quotes.append(agr_quote)
        return agr_quotes

    @classmethod
    def sanitize(cls, quotes: List['Quote'], domain: Any = None) -> List['Quote']:
        if len(quotes) == 0:
            return []

        # Trim zero volume quotes
        quotes = cls.trim_list(quotes, domain=domain)
        if len(quotes) == 0:
            return []

        # Fill empty
        quotes = cls.fill_empty(quotes, domain=domain)

        # double check expected length
        if not Quote.is_contiguous(quotes):
            raise Exception(f'Quotes are not contiguous after sanitisation')

        return quotes

    @classmethod
    def empty_between(cls, q0: 'Quote', q1: 'Quote') -> List['Quote']:
        """
        Returns empty quotes between `q0` and `q1`.
        """
        resolution = q0.resolution
        if q1.resolution != q1.resolution:
            raise Exception('Quote resolutions must be equal')

        missing_interval = q1.start_date - q0.end_date
        if missing_interval == 0:
            return []
        elif missing_interval < 0:
            raise Exception('Quotes must be in ascending order')

        ohlc = [q0.close] * 4
        quotes = []
        domain = Interval.intersection([
            q0.domain.rest_to_positive_infinity(),
            q1.domain.rest_to_negative_infinity()
        ])
        assert domain.is_finite
        for span in resolution.iterate(domain, start_open=domain.start_open):
            q = Quote(
                ohlc,
                date=span.start,
                volume=0.0,
                resolution=resolution
            )
            quotes.append(q)

        if quotes[-1].end_date > q1.start_date:
            raise Exception(f'Unregular quote distance between filled quote {quotes[-1]} and {q1}')
        return quotes

    @classmethod
    def fill_empty(cls, quotes: List['Quote'], domain: Any = None) -> List['Quote']:
        """
        Returns a new list of quotes with gaps
        filled with empty quotes.

        If a domain is specified, it is assumed to be
        a superset of the quotes domain.
        """
        if not bool(quotes):
            if domain is None:
                return []
            raise ValueError('Must specify an non empty quote list')
        quotes = list(quotes)

        if domain is None:
            domain = cls.list_domain(quotes)

        if not Quote.is_contiguous(quotes):
            # Fill between quotes
            for i in reversed(range(1, len(quotes))):
                q0 = quotes[i - 1]
                q1 = quotes[i]
                if q0.end_date < q1.start_date:
                    # add missing quotes
                    filler = cls.empty_between(q0, q1)
                    quotes[i:i] = filler

        # Fill start
        q = quotes[0]
        start_domain = q.domain.rest_to_negative_infinity() & domain
        if not start_domain.is_empty:
            start_quotes = cls.empty_list(q.open, q.resolution, start_domain)
            quotes[0:0] = start_quotes
        
        # Fill end
        q = quotes[-1]
        end_domain = q.domain.rest_to_positive_infinity() & domain
        if not end_domain.is_empty:
            end_quotes = cls.empty_list(q.close, q.resolution, end_domain)
            iend = len(quotes)
            quotes[iend:iend] = end_quotes
        
        return quotes

    @classmethod
    def empty_list(cls, price: float, resolution: Any, domain: Any) -> List['Quote']:
        domain = Interval.parse(domain)
        quotes: List[Quote] = []
        if not domain.is_empty:
            if not domain.is_finite:
                raise ValueError('Must specify a finite domain')
            resolution = Duration.parse(resolution)
            ohlc = [price] * 4
            for span in resolution.iterate(domain, start_open=DOMAIN_START_OPEN):
                q = Quote(
                    ohlc,
                    date=span.start,
                    volume=0.0,
                    resolution=resolution
                )
                quotes.append(q)
        return quotes

    @staticmethod
    def aggregated_list(quotes1, quotes2):
        """
        Merges quotes by merging high, low data and volume
        by using `min` and `max` where appropriate.

        Open is taken from the quote with the higher volume.

        Close is taken from the second list.
        """
        if len(quotes1) == 0:
            return list(quotes2)
        if len(quotes2) == 0:
            return list(quotes1)
        quotes = list(quotes1)
        for q2 in quotes2:
            i = Quote.bisect(quotes, q2)
            if i < len(quotes):
                q1 = quotes[i]
            else:
                q1 = None
            if q1 is not None and q1.date == q2.date:
                # merge
                if q1.resolution != q2.resolution:
                    raise Exception('Quote resolutions must be the same')
                h = max(q1.high, q2.high)
                l = min(q1.low, q2.low)
                v = max(q1.volume, q2.volume)
                o = q2.open if q2.volume > q1.volume else q1.open
                c = q2.close
                q = Quote(o, h, l, c, date=q2.date,
                          volume=v, resolution=q2.resolution)
                quotes[i] = q
            else:
                # insert
                quotes.insert(i, q2)
        return quotes

    @staticmethod
    def merge_lists(quotes1, quotes2):
        """
        Returns a merged list with duplicates removed. The second list takes precedence.

        Assumes that the quotes are contiguous in both lists.
        """
        if len(quotes1) == 0:
            return list(quotes2)
        if len(quotes2) == 0:
            return list(quotes1)
        quotes = list(quotes1)
        i0 = Quote.bisect(quotes, quotes2[0])
        i1 = Quote.bisect(quotes, quotes2[-1]) + 1
        quotes[i0:i1] = quotes2
        return quotes

    @classmethod
    def list_domain(cls, quotes):
        if len(quotes) == 0:
            return Interval.empty()
        return Interval.union([quotes[0].domain, quotes[-1].domain])

    @staticmethod
    def inside_domain(quotes, domain):
        """
        Returns quotes inside the domain.
        """
        domain = Interval.parse(domain)
        if domain.is_empty:
            return []
        if domain.is_infinite:
            return list(quotes)
        quotes_len = len(quotes)
        if quotes_len == 0:
            return []
        i0 = max(0, Quote.bisect(quotes, domain.start) - 1)
        i1 = min(quotes_len, Quote.bisect(quotes, domain.end) + 1)
        matching_quotes = quotes[i0:i1]

        while len(matching_quotes) != 0 and not domain.intersects(matching_quotes[0].domain):
            del matching_quotes[0]
        while len(matching_quotes) != 0 and not domain.intersects(matching_quotes[-1].domain):
            del matching_quotes[-1]

        return matching_quotes

    @classmethod
    def trim_list(cls, quotes: List['Quote'], domain: Any = None) -> List['Quote']:
        """
        Removes empty quotes from the start and end of the list.

        If a domain is specified, only empty quotes outside of the
        domain are removed.
        """
        if len(quotes) == 0:
            return []
        i0: Optional[int] = None
        i1: Optional[int] = None
        r = range(len(quotes))
        if domain is not None:
            domain = Interval.parse(domain)

        for i in r:
            q = quotes[i]
            if not q.is_empty or (domain is not None and domain.intersects(q.domain)):
                i0 = i
                break
        if i0 is None:
            return []

        for i in reversed(r):
            q = quotes[i]
            if not q.is_empty or (domain is not None and domain.intersects(q.domain)):
                i1 = i
                break
        assert i1 is not None
        return quotes[i0:i1 + 1]

    @staticmethod
    def bisect(a, q, lo=0, hi=None):
        """
        Return insert index for quote `q` in list `a`, and keep it sorted assuming `a` is sorted.
        If `q` is already in `a`, insert it to the left of the leftmost `q`.
        Optional args `lo` (default `0`) and `hi` (default `len(a)`) bound the
        slice of `a` to be searched.
        """

        if lo < 0:
            raise ValueError('lo must be non-negative')

        if isinstance(q, Quote):
            date = q.date
        else:
            date = q

        a_len = len(a)
        if hi is None:
            hi = a_len
        while lo < hi:
            mid = (lo + hi) // 2
            if a[mid].date < date:
                lo = mid + 1
            else:
                hi = mid
        return lo

    @staticmethod
    def from_cryptocompare_json(json):
        DATE_KEY = 'time'
        OPEN_KEY = 'open'
        HIGH_KEY = 'high'
        LOW_KEY = 'low'
        CLOSE_KEY = 'close'
        VOLUME_KEY = 'volumeto'

        return Quote(json[OPEN_KEY], json[HIGH_KEY], json[LOW_KEY], json[CLOSE_KEY], date=json[DATE_KEY], volume=json[VOLUME_KEY])

    @classmethod
    def _with_normalized_data(cls, data):
        ohlc = []
        for key in OHLC_KEYS:
            ohlc.append(data[key])
            del data[key]
        return Quote(*ohlc, **data)

    @classmethod
    def parse(cls, *args, **kwargs) -> 'Quote':
        if len(args) == 1:
            q = args[0]
            if isinstance(q, Quote):
                return q
        data = cls.normalize_data(*args, **kwargs)
        return cls._with_normalized_data(data)

    @classmethod
    def parse_many(cls, data) -> List['Quote']:
        # Get dicts in case there is missing
        # resolution data
        dicts = [cls.normalize_data(x) for x in data]

        # Find resolution
        res = None
        for i, d in enumerate(dicts):
            if d['res'] is not None:
                res = d['res']
                break
            elif i != 0:
                # Compare dates
                d_prev = dicts[i - 1]
                if d['date'] is not None and d_prev['date'] is not None:
                    res = Duration(d['date'] - d_prev['date'])
                    break
        if res is None:
            raise ValueError('Unable to infer quote resolution')

        # Apply resolution, dates and create quotes
        quotes = []
        last_quote = None
        for i, d in enumerate(dicts):
            if d['res'] is None:
                d['res'] = res
            elif d['res'] != res:
                raise ValueError('Mixed resolution')
            if d['date'] is None:
                if i == 0:
                    raise ValueError('Unable to infer quote date')
                prev_date = dicts[i - 1]['date']
                d['date'] = res.next(prev_date)
            q = cls._with_normalized_data(d)
            if last_quote is not None:
                if q.domain.intersects(last_quote.domain):
                    raise ValueError('Quote dates are overlapping')
            quotes.append(q)
            last_quote = q
        return quotes

    @classmethod
    def normalize_data(cls, *args, **kwargs):
        args = test_util.flatten(args)
        raw_dict = dict(kwargs)
        numbers = []
        v = None
        t = None
        res = None
        for i, x in enumerate(args):
            if x is None:
                raise Exception(f'Unexpected None: {args} {kwargs}')
            elif isinstance(x, Quote):
                raw_dict.update(x.get_values())
            elif isinstance(x, Mapping):
                raw_dict.update(x)
            elif isinstance(x, (str, datetime.datetime, datetime.date, arrow.Arrow)):
                t = test_util.timestamp(x)
            elif isinstance(x, Duration):
                res = x
            elif isinstance(x, datetime.timedelta):
                res = Duration(x)
            elif isinstance(x, Number):
                numbers.append(x)
            else:
                raise Exception(f'Unexpected value type: {args} {kwargs}')

        if len(numbers) == 5:
            v = numbers[4]
            del numbers[4]
        elif len(numbers) > 5:
            raise Exception(f'Too many numbers: {args} {kwargs}')

        if len(numbers) != 0:
            o = numbers[0]
            h = max(numbers)
            l = min(numbers)
            c = numbers[-1]
        else:
            o = None
            h = None
            l = None
            c = None

        return {
            'open': test_util.value_for_any_key(raw_dict, ['open', 'o'], default=o),
            'high': test_util.value_for_any_key(raw_dict, ['high', 'h'], default=h),
            'low': test_util.value_for_any_key(raw_dict, ['low', 'l'], default=l),
            'close': test_util.value_for_any_key(raw_dict, ['close', 'c'], default=c),
            'volume': test_util.value_for_any_key(raw_dict, ['volume', 'vol', 'v'], default=v),
            'date': test_util.value_for_any_key(raw_dict, ['date', 't'], default=t, map=test_util.timestamp),
            'res': test_util.value_for_any_key(raw_dict, ['resolution', 'res', 'period'], default=res)
        }

    @classmethod
    def mock(cls, quotes, t_start=0, t_step=86400.0, volume=1):
        dicts = []
        t_start = test_util.timestamp(t_start)
        t_step = Duration.parse(t_step)
        t = t_step.floor(t_start)
        for q in quotes:
            d = cls.normalize_data(q)

            if d['volume'] is None:
                d['volume'] = volume

            if d['date'] is None:
                d['date'] = t
            else:
                t = d['date']

            if d['res'] is None:
                d['res'] = t_step

            dicts.append(d)
            t = t_step.next(t)
        return cls.parse_many(dicts)

    @classmethod
    def mock_ohlcv(cls, quotes, t_start=0, t_step=86400.0, volume=1):
        return cls.to_ohlcv(cls.mock(quotes, t_start, t_step, volume))

    @classmethod
    def mock_ohlcv_points(cls, quotes, t_start=0, t_step=86400.0, volume=1):
        return cls.to_ohlcv_points(cls.mock(quotes, t_start, t_step, volume))
