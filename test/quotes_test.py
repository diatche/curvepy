import pytest
import math
import numpy as np
from time import time
from pytest import approx
from func.quotes import Quotes
from intervalpy import Interval
from .quote import Quote


def test_quotes():
    original_ohlc = [
        (1, 2.2, 0.9, 2),
        (2, 3.1, 1.9, 3),
        (3, 5.1, 2.9, 5)
    ]
    f = Quotes(1, quotes=Quote.mock(
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
    assert f(10).date == 10
    assert f(10.5).date == 10
    assert f(11).date == 11
    assert f(11.5).date == 11
    assert f(12).date == 12
    assert f(12.5) is None


def test_map():
    original_ohlc = [
        (1, 2.2, 0.9, 2),
        (2, 3.1, 1.9, 3),
        (3, 5.1, 2.9, 5)
    ]
    f = Quotes(1, quotes=Quote.mock(
        original_ohlc, t_start=10, t_step=1)).map(lambda q: q.close, skip_none=True)

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

    f = Quotes(step, quotes=Quote.mock(
        original_ohlc, t_start=start, t_step=step))
    x = start
    for i in range(1, len(original_ohlc) - 1):
        x1 = f.x_next(x)
        assert x1 > x
        assert x1 == start + i * step
        x = x1


def test_missing_quotes():
    quotes = Quote.mock([
        (1, 2.2, 0.9, 2),
        (2, 3.1, 1.9, 3),
        (3, 5.1, 2.9, 5)
    ] * 10)
    del quotes[8]
    with pytest.raises(Exception):
        Quotes(86400.0, quotes=quotes)


def test_sample():
    original_quotes = Quote.mock([
        (1, 2.2, 0.9, 2),
        (2, 3.1, 1.9, 3),
        (3, 5.1, 2.9, 5)
    ], t_start=10, t_step=1)
    f = Quotes(1, quotes=original_quotes)

    quotes = f.sample()
    assert quotes == original_quotes

    quotes = f.sample(domain=Interval.open(11, 12))
    assert quotes == original_quotes[1:2]


def test_sample_points():
    original_quotes = Quote.mock([
        (1, 2.2, 0.9, 2),
        (2, 3.1, 1.9, 3),
        (3, 5.1, 2.9, 5)
    ], t_start=0, t_step=1)
    f = Quotes(1, quotes=original_quotes)

    ps = f.sample_points()
    assert ps == list(enumerate(original_quotes))

    ps = f.sample_points(domain=Interval.open_closed(1, 2))
    assert ps == [(2, original_quotes[2])]

    ps = f.sample_points(domain=Interval.closed(1, 2))
    assert ps == [
        (1, original_quotes[1]),
        (2, original_quotes[2])
    ]

    ps = f.sample_points(domain=Interval.open(2, 5))
    assert ps == []

    ps = f.sample_points(domain=Interval.closed(0, 1))
    assert ps == [
        (0, original_quotes[0]),
        (1, original_quotes[1])
    ]


def test_close():
    ps = Quotes(1, quotes=Quote.mock([
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


def test_high():
    ps = Quotes(1, quotes=Quote.mock([
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
    ps = Quotes(1, quotes=Quote.mock([
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
    ps = Quotes(1, quotes=Quote.mock([
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
    ps = Quotes(1, quotes=Quote.mock([
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


def test_ohlc():
    ps = Quotes(1, quotes=Quote.mock([
        (1, 2.2, 0.9, 2),
        (2, 3.1, 1.9, 3)
    ], t_step=1)).ohlc
    assert ps.domain.start == 0
    assert ps.domain.end == 2

    assert ps.x_next(-1) == 0
    assert ps.x_next(-0.1, min_step=0.01) == 0
    assert ps.x_next(0) == approx(0.333, rel=0.01)
    assert ps.x_next(0.1) == approx(0.333, rel=0.01)
    assert ps.x_next(0.333, min_step=0.01) == approx(0.667, rel=0.01)
    assert ps.x_next(0.4, min_step=0.01) == approx(0.667, rel=0.01)
    assert ps.x_next(0.667, min_step=0.01) == 1
    assert ps.x_next(0.8, min_step=0.01) == 1
    assert ps.x_next(1.8, min_step=0.01) == 2
    assert ps.x_next(2) is None

    assert ps.x_previous(0) is None
    assert ps.x_previous(0.1) == 0
    assert ps.x_previous(0.333, min_step=0.01) == 0
    assert ps.x_previous(0.4, min_step=0.01) == approx(0.333, rel=0.01)
    assert ps.x_previous(0.667, min_step=0.01) == approx(0.333, rel=0.01)
    assert ps.x_previous(0.8, min_step=0.01) == approx(0.667, rel=0.01)
    assert ps.x_previous(1, min_step=0.01) == approx(0.667, rel=0.01)
    assert ps.x_previous(2.1, min_step=0.01) == 2

    assert ps(0) == approx(1, rel=0.01)
    assert ps(0.111) == approx(1 * 0.667 + 0.9 * 0.333, rel=0.01)
    assert ps(0.3334) == approx(0.9, rel=0.01)
    assert ps(0.667) == approx(2.2, rel=0.01)
    assert ps(0.888) == approx(2 * 0.667 + 2.2 * 0.333, rel=0.01)
    assert ps(1) == approx(2, rel=0.01)
    assert ps(1.111) == approx(2 * 0.667 + 1.9 * 0.333, rel=0.01)
    assert ps(1.333) == approx(1.9, rel=0.01)
    assert ps(1.667) == approx(3.1, rel=0.01)
    assert ps(1.888) == approx(3 * 0.667 + 3.1 * 0.333, rel=0.01)
    assert ps(2) == approx(3, rel=0.01)

    assert np.allclose(ps.sample_points(), [(
        0, 1), (0.3334, 0.9), (0.667, 2.2), (1, 2), (1.333, 1.9), (1.667, 3.1), (2, 3)], rtol=0.01)


def test_ohlc_updates():
    quotes = Quote.mock([
        (1, 2.2, 0.9, 2),
        (2, 3.1, 1.9, 3)
    ], t_step=1)
    f = Quotes(1, quotes=[quotes[0]])
    ps = f.ohlc
    assert ps.domain.start == 0
    assert ps.domain.end == 1
    assert ps(0.3334) == approx(0.9, rel=0.01)
    assert ps(0.667) == approx(2.2, rel=0.01)
    assert ps(1) == approx(2, rel=0.01)
    assert ps(1.1) is None

    f.append(quotes[1])
    assert ps.domain.end == 2
    assert ps(1.333) == approx(1.9, rel=0.01)
    assert ps(1.667) == approx(3.1, rel=0.01)
    assert ps(2) == approx(3, rel=0.01)


def test_append_to_empty():
    f = Quotes(1)
    ps = f.close
    f.append_list(Quote.mock([
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
    f.append_list(Quote.mock([
        (1, 2.2, 0.9, 2),
        (2, 3.1, 1.9, 3),
        (3, 5.1, 2.9, 5)
    ], t_start=10, t_step=1))
    assert callback_count == 1


def test_offset_close():
    ps = Quotes(1, quotes=Quote.mock([
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

    mock_quotes = Quote.mock([
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


def test_ohlc_points_during_update():
    f = Quotes(1)
    points = f.ohlc
    callback_count = 0
    assert np.array_equal(points.sample_points(), [])

    def callback(*args):
        nonlocal callback_count
        callback_count += 1
        assert points(10) == 1
        assert points(13) == 5

    points.add_observer(end=callback)
    f.append_list(Quote.mock([
        (1, 2.2, 0.9, 2),
        (2, 3.1, 1.9, 3),
        (3, 5.1, 2.9, 5)
    ], t_start=10, t_step=1))
    assert callback_count == 1


def test_extend_close():
    ps = Quotes(1, quotes=Quote.mock([
        (1, 2.2, 0.9, 2),
        (2, 3.1, 1.9, 3)
    ], t_step=1)).close.extension('tangent', start=True, end=True)
    assert ps(-1) == 1
    assert ps(0) == 2
    assert ps(1) == 3
    assert ps(2) == 4
    assert ps(3) == 5


def test_extend_ohlc():
    ps = Quotes(1, quotes=Quote.mock([
        (1, 2.33, 0.66, 2),
        (2, 3.33, 1.66, 3)
    ], t_step=1)).ohlc.extension('tangent', start=True, end=True)
    assert ps(-1) == approx(2, abs=0.03)
    assert ps(0) == 1
    assert ps(2) == 3
    assert ps(3) == approx(2, abs=0.03)


def test_offset_extend_ohlc():
    ps = Quotes(1, quotes=Quote.mock([
        (1, 2.33, 0.66, 2),
        (2, 3.33, 1.66, 3)
    ], t_step=1)).ohlc.offset(10).extension('tangent', start=True, end=True)
    assert ps(9) == approx(2, abs=0.03)
    assert ps(10) == 1
    assert ps(12) == 3
    assert ps(13) == approx(2, abs=0.03)


def test_multiple_nested_quotes_update():
    duration = 1
    quotes = Quotes(duration)
    jaw = quotes.close
    teeth = quotes.close
    ave = (jaw * 13 + teeth * 8) / 21

    mock_quotes = Quote.mock(list(np.arange(1, 25)), t_step=1)
    for q in mock_quotes:
        quotes.append(q)
        assert jaw.is_updating is False
        assert teeth.is_updating is False
        assert ave.is_updating is False
        _ = ave.domain

    assert ave.domain == Interval.closed(0, 23)
    assert ave(0) == 1
