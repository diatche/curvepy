import pytest
import math
import numpy as np
from time import time
from curvepy.quotes import Quotes, OPEN, HIGH, LOW, CLOSE, VOLUME
from intervalpy import Interval
from .quote import Quote


def test_quotes():
    original_ohlc = [
        (1, 2.2, 0.9, 2),
        (2, 3.1, 1.9, 3),
        (3, 5.1, 2.9, 5)
    ]
    f = Quotes(1, quote_points=Quote.mock_ohlcv_points(
        original_ohlc, t_start=10, t_step=1))

    assert f.domain.start == 10
    assert f.domain.end == 12

    assert f.x_next(9) == 10
    assert f.x_next(10) == 11
    assert f.x_next(10.5) == 11
    assert f.x_next(11) == 12
    assert f.x_next(11.5) == 12
    assert f.x_next(12) is None

    assert f.x_previous(10) is None
    assert f.x_previous(10.5) == 10
    assert f.x_previous(12.5) == 12
    assert f.x_previous(13) == 12

    assert f(9) is None
    assert f(10)[CLOSE] == 2
    assert f(10.5)[CLOSE] == 2
    assert f(11)[CLOSE] == 3
    assert f(11.5)[CLOSE] == 3
    assert f(12)[CLOSE] == 5
    assert f(12.5) is None


def test_quotes_encoder():
    def encoder(q):
        return (q['date'], (q['open'], q['high'], q['low'], q['close'], q['volume']))
    points = [{ "date": 1, "open": 2, "high": 3, "low": 4, "close": 5, "volume": 6 }]
    f = Quotes(1, quote_points=points, encoder=encoder)
    p = f.y(1)
    assert p[OPEN] == 2
    assert p[HIGH] == 3
    assert p[LOW] == 4
    assert p[CLOSE] == 5
    assert p[VOLUME] == 6


def test_map():
    original_ohlc = [
        (1, 2.2, 0.9, 2),
        (2, 3.1, 1.9, 3),
        (3, 5.1, 2.9, 5)
    ]
    f = Quotes(1, quote_points=Quote.mock_ohlcv_points(
        original_ohlc, t_start=10, t_step=1)).map(lambda q: q[CLOSE], skip_none=True)

    assert f.domain.start == 10
    assert f.domain.end == 12

    assert f.x_next(9) == 10
    assert f.x_next(10) == 11
    assert f.x_next(10.5) == 11
    assert f.x_next(11) == 12
    assert f.x_next(12) is None

    assert f.x_previous(10) is None
    assert f.x_previous(10.5) == 10
    assert f.x_previous(12.5) == 12
    assert f.x_previous(13) == 12

    assert f(9) is None
    assert f(10) == 2
    assert f(10.5) == 2
    assert f(11) == 3
    assert f(11.5) == 3
    assert f(12) == 5


def test_longer_data():
    start = math.floor(time() / 86400) * 86400.0
    step = 86400.0
    repeats = 100
    original_ohlc = [
        (1, 2.2, 0.9, 2),
        (2, 3.1, 1.9, 3),
        (3, 5.1, 2.9, 5)
    ] * repeats

    f = Quotes(step, quote_points=Quote.mock_ohlcv_points(
        original_ohlc, t_start=start, t_step=step))
    x = start
    for i in range(1, len(original_ohlc) - 1):
        x1 = f.x_next(x)
        assert x1 > x
        assert x1 == start + i * step
        x = x1


def test_missing_quotes():
    quotes = Quote.mock_ohlcv_points([
        (1, 2.2, 0.9, 2),
        (2, 3.1, 1.9, 3),
        (3, 5.1, 2.9, 5)
    ] * 10)
    del quotes[8]
    with pytest.raises(Exception):
        Quotes(86400.0, quote_points=quotes)


def test_sample():
    original_quotes_points = Quote.mock_ohlcv_points([
        (1, 2.2, 0.9, 2),
        (2, 3.1, 1.9, 3),
        (3, 5.1, 2.9, 5)
    ], t_start=10, t_step=1)
    original_quotes = [p[1] for p in original_quotes_points]
    f = Quotes(1, quote_points=original_quotes_points)

    quotes = f.sample()
    assert quotes == original_quotes

    quotes = f.sample(domain=Interval.open(11, 12))
    assert quotes == original_quotes[1:2]


def test_sample_points():
    original_quotes_points = Quote.mock_ohlcv_points([
        (1, 2.2, 0.9, 2),
        (2, 3.1, 1.9, 3),
        (3, 5.1, 2.9, 5)
    ], t_start=0, t_step=1)
    f = Quotes(1, quote_points=original_quotes_points)

    ps = f.sample_points()
    assert ps == original_quotes_points

    ps = f.sample_points(domain=Interval.open_closed(1, 2))
    assert ps == original_quotes_points[1:3]

    ps = f.sample_points(domain=Interval.closed(1, 2))
    assert ps == original_quotes_points[1:3]

    ps = f.sample_points(domain=Interval.closed(3, 4))
    assert ps == []

    ps = f.sample_points(domain=Interval.closed(-1, 0))
    assert ps == original_quotes_points[0:1]


def test_close():
    ps = Quotes(1, quote_points=Quote.mock_ohlcv_points([
        (1, 2.2, 0.9, 2),
        (2, 3.1, 1.9, 3),
        (3, 5.1, 2.9, 5)
    ], t_start=10, t_step=1)).close
    assert ps.domain.start == 10
    assert ps.domain.end == 12

    assert ps.x_next(9) == 10
    assert ps.x_next(10) == 11
    assert ps.x_next(10.5) == 11
    assert ps.x_next(11.5) == 12
    assert ps.x_next(12) is None

    assert ps.sample_points() == [(10, 2), (11, 3), (12, 5)]
    assert ps(9.5) is None
    assert ps(10.5) == 2
    assert ps(11.5) == 3
    assert ps(12.5) is None


def test_open():
    ps = Quotes(1, quote_points=Quote.mock_ohlcv_points([
        (1, 2.2, 0.9, 2),
        (2, 3.1, 1.9, 3),
        (3, 5.1, 2.9, 5)
    ], t_start=10, t_step=1)).open
    assert ps.domain.start == 10
    assert ps.domain.end == 12

    assert ps.x_next(9) == 10
    assert ps.x_next(10) == 11
    assert ps.x_next(10.5) == 11
    assert ps.x_next(11.5) == 12
    assert ps.x_next(12) is None

    assert ps.sample_points() == [(10, 1), (11, 2), (12, 3)]
    assert ps(9.5) is None
    assert ps(10.5) == 1
    assert ps(11.5) == 2
    assert ps(12.5) is None


def test_high():
    ps = Quotes(1, quote_points=Quote.mock_ohlcv_points([
        (1, 2.2, 0.9, 2),
        (2, 3.1, 1.9, 3),
        (3, 5.1, 2.9, 5)
    ], t_start=10, t_step=1)).high
    assert ps.domain.start == 10
    assert ps.domain.end == 12

    assert ps.x_next(9) == 10
    assert ps.x_next(10) == 11
    assert ps.x_next(10.5) == 11
    assert ps.x_next(11.5) == 12
    assert ps.x_next(12) is None

    assert ps.sample_points() == [(10, 2.2), (11, 3.1), (12, 5.1)]
    assert ps(9.5) is None
    assert ps(10.5) == 2.2
    assert ps(11.5) == 3.1
    assert ps(12.5) is None


def test_low():
    ps = Quotes(1, quote_points=Quote.mock_ohlcv_points([
        (1, 2.2, 0.9, 2),
        (2, 3.1, 1.9, 3),
        (3, 5.1, 2.9, 5)
    ], t_start=10, t_step=1)).low
    assert ps.domain.start == 10
    assert ps.domain.end == 12

    assert ps.x_next(9) == 10
    assert ps.x_next(10) == 11
    assert ps.x_next(10.5) == 11
    assert ps.x_next(11.5) == 12
    assert ps.x_next(12) is None

    assert ps.sample_points() == [(10, 0.9), (11, 1.9), (12, 2.9)]
    assert ps(9.5) is None
    assert ps(10.5) == 0.9
    assert ps(11.5) == 1.9
    assert ps(12.5) is None


def test_hl2():
    ps = Quotes(1, quote_points=Quote.mock_ohlcv_points([
        (1, 2.2, 0.9, 2),
        (2, 3.1, 1.9, 3),
        (3, 5.1, 2.9, 5)
    ], t_start=10, t_step=1)).hl2
    assert ps.domain.start == 10
    assert ps.domain.end == 12

    assert ps.x_next(9) == 10
    assert ps.x_next(10) == 11
    assert ps.x_next(10.5) == 11
    assert ps.x_next(11.5) == 12
    assert ps.x_next(12) is None

    assert ps.sample_points() == [(10, 1.55), (11, 2.5), (12, 4)]
    assert ps(9.5) is None
    assert ps(10.5) == 1.55
    assert ps(11.5) == 2.5
    assert ps(12.5) is None


def test_volume():
    ps = Quotes(1, quote_points=Quote.mock_ohlcv_points([
        (1, 2.2, 0.9, 2, 10),
        (2, 3.1, 1.9, 3, 20),
        (3, 5.1, 2.9, 5, 30)
    ], t_start=10, t_step=1)).volume
    assert ps.domain.start == 10
    assert ps.domain.end == 12

    assert ps.x_next(9) == 10
    assert ps.x_next(10) == 11
    assert ps.x_next(10.5) == 11
    assert ps.x_next(11.5) == 12
    assert ps.x_next(12) is None

    assert ps.sample_points() == [(10, 10), (11, 20), (12, 30)]
    assert ps(9.5) is None
    assert ps(10.5) == 10
    assert ps(11.5) == 20
    assert ps(12.5) is None


def test_append_to_empty():
    f = Quotes(1)
    ps = f.close
    f.append_list(Quote.mock_ohlcv_points([
        (1, 2.2, 0.9, 2),
        (2, 3.1, 1.9, 3),
        (3, 5.1, 2.9, 5)
    ], t_start=10, t_step=1))
    assert ps.sample_points() == [(10, 2), (11, 3), (12, 5)]


def test_close_points_during_update():
    f = Quotes(1)
    points = f.close
    callback_count = 0
    assert np.array_equal(points.sample_points(), [])

    def callback(*args):
        nonlocal callback_count
        callback_count += 1
        assert points.sample_points() == [(10, 2), (11, 3), (12, 5)]

    points.add_observer(end=callback)
    f.append_list(Quote.mock_ohlcv_points([
        (1, 2.2, 0.9, 2),
        (2, 3.1, 1.9, 3),
        (3, 5.1, 2.9, 5)
    ], t_start=10, t_step=1))
    assert callback_count == 1


def test_offset_close():
    ps = Quotes(1, quote_points=Quote.mock_ohlcv_points([
        (1, 2.2, 0.9, 2),
        (2, 3.1, 1.9, 3)
    ], t_step=1)).close.offset(10)
    assert ps.domain == Interval.closed(10, 11)
    assert ps(9) is None
    assert ps(10) == 2
    assert ps(11) == 3
    assert ps(12) is None


def test_offset_close_update_from_empty():
    quotes = Quotes(1)
    ps = quotes.close.offset(10)
    assert ps.domain.is_empty

    mock_quotes = Quote.mock_ohlcv_points([
        (1, 2.2, 0.9, 2),
        (2, 3.1, 1.9, 3)
    ], t_step=1)

    for q in mock_quotes:
        quotes.append(q)
        _ = ps.domain

    assert ps.domain == Interval.closed(10, 11)
    assert ps(9) is None
    assert ps(10) == 2
    assert ps(11) == 3
    assert ps(12) is None


def test_extend_close():
    ps = Quotes(1, quote_points=Quote.mock_ohlcv_points([
        (1, 2.2, 0.9, 2),
        (2, 3.1, 1.9, 3)
    ], t_step=1)).close.extension('tangent', start=True, end=True)
    assert ps(-1) == 1
    assert ps(0) == 2
    assert ps(1) == 3
    assert ps(2) == 4
    assert ps(3) == 5


def test_multiple_nested_quotes_update():
    duration = 1
    quotes = Quotes(duration)
    jaw = quotes.close
    teeth = quotes.close
    ave = (jaw * 13 + teeth * 8) / 21

    mock_quotes = Quote.mock_ohlcv_points(list(np.arange(1, 25)), t_step=1)
    for q in mock_quotes:
        quotes.append(q)
        assert jaw.is_updating is False
        assert teeth.is_updating is False
        assert ave.is_updating is False
        _ = ave.domain

    assert ave.domain == Interval.closed(0, 23)
    assert ave(0) == 1
