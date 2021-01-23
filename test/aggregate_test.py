import pytest
import numpy as np
from curvepy.aggregate import Aggregate
from curvepy.constant import Constant
from curvepy.points import Points
from curvepy.generic import Generic
from intervalpy import Interval
from . import test_util


def test_infinite():
    c1 = Constant(1)

    c2 = c1.add(3)
    assert c2(0) == 4
    assert np.array_equal(c2.sample_points(domain=(0, 2)), [(0, 4), (2, 4)])

    c3 = c1.subtract(4)
    assert c3(0) == -3
    assert np.array_equal(c3.sample_points(domain=(0, 2)), [(0, -3), (2, -3)])


def test_finite():
    f1 = Generic(lambda x: 3, domain=(0, 2))
    f2 = Generic(lambda x: 2, domain=(1, 3))

    f = f1.add(f2)
    assert f(0) is None
    assert f(0.9) is None
    assert f(1) == 5
    assert f(2) == 5
    assert f(2.1) is None

    assert np.allclose(f.sample_points(
        domain=(0, 3), min_step=1), [(1, 5), (2, 5)])

    f = f1.subtract(f2)
    assert f(1) == 1


def test_subset():
    f1 = Generic(lambda x: 3, domain=(1, 2), min_step=1)
    f2 = Generic(lambda x: 2, domain=(0, 3), min_step=1)

    f = f1.add(f2)
    assert f(0) is None
    assert f(0.9) is None
    assert f(1) == 5
    assert f(2) == 5
    assert f(2.1) is None

    assert f.sample_points() == [(1, 5), (2, 5)]

    f = f1.subtract(f2)
    assert f(1) == 1


def test_none_union():
    p1 = Points([(0, None), (1, None)])
    f = Aggregate([p1], tfm=lambda x, ys: ys[0], union=True)
    assert f.domain.start == 0
    assert f.domain.end == 1
    assert f(0) is None
    assert f(1) is None


def test_empty_union():
    p1 = Points([])
    f = Aggregate([p1], tfm=lambda x, ys: ys[0], union=True)
    assert f.domain.is_empty
    assert f(0) is None
    assert f(1) is None


def test_step():
    p1 = Points([(0, 1), (1, 1), (2, 1), (3, 1), (4, 1)])
    p2 = Points([(0, 2), (2, 2), (4, 2)])
    f = Aggregate([p1, p2], tfm=lambda x, ys: sum(ys))

    c = 100
    for i in range(c):
        assert f(i / float(c) * f.domain.length) == 3
        assert ((p2 + p1) - p2)(i / float(c) * f.domain.length) == 1

    assert f.x_next(-0.5) == 0
    assert f.x_next(0) == 1
    assert f.x_next(0.5) == 1
    assert f.x_next(1) == 2
    assert f.x_next(1.5) == 2
    assert f.x_next(3.5) == 4
    assert f.x_next(4) is None

    assert f.x_previous(0) is None
    assert f.x_previous(0.5) == 0
    assert f.x_previous(1) == 0
    assert f.x_previous(1.5) == 1
    assert f.x_previous(3.5) == 3
    assert f.x_previous(4) == 3
    assert f.x_previous(4.5) == 4


def test_update():
    p1 = Points([(0, 1), (1, 1)])
    p2 = Points([(2, 2), (4, 2)])

    f = Aggregate([p1, p2], tfm=lambda x, ys: sum(ys), union=False)
    assert f.domain.is_empty
    assert f(0) is None
    assert f(1.5) is None
    assert f(3) is None

    p1.append((2, 1))
    assert f.domain.start == 2
    assert f.domain.end == 2
    assert not f.domain.start_open
    assert not f.domain.end_open
    assert f(2) == 3
    assert f.is_updating is False

    p1.append((3, 1))
    assert f.domain.start == 2
    assert f.domain.end == 3
    assert not f.domain.start_open
    assert not f.domain.end_open
    assert f(2) == 3
    assert f(3) == 3
    assert f.is_updating is False

    p1.append((4, 1))
    assert f.domain.start == 2
    assert f.domain.end == 4
    assert not f.domain.start_open
    assert not f.domain.end_open
    assert f(4) == 3
    assert f.is_updating is False


def test_update_from_empty():
    p1 = Points([])
    f = Aggregate([p1], tfm=lambda x, ys: sum(ys))
    assert f(0) is None

    p1.append((0, 1))
    assert f(0) == 1

    p1.append((1, 2))
    assert f(1) == 2

    p1.append((2, 3))
    assert f(2) == 3


def test_nested_update():
    p1 = Points([(0, 1), (1, 1)])
    p2 = Points([(2, 2), (4, 2)])

    f = Aggregate([p1 * 2, p2 * 2], tfm=lambda x, ys: sum(ys))
    assert f.domain.is_empty
    assert f(0) is None
    assert f(1.5) is None
    assert f(3) is None

    p1.append((2, 1))
    assert f.domain.start == 2
    assert f.domain.end == 2
    assert not f.domain.start_open
    assert not f.domain.end_open
    assert f(2) == 6

    p1.append((3, 1))
    assert f.domain.start == 2
    assert f.domain.end == 3
    assert not f.domain.start_open
    assert not f.domain.end_open
    assert f(2) == 6
    assert f(3) == 6


def test_multiple_nested_update():
    p1 = Points([(0, 1), (1, 1)])
    p2 = Points([(2, 2), (4, 2)])

    f = (p1.offset(10) * 2 + p2.offset(10) * 2) / 2
    assert f.domain.is_empty
    assert f(10) is None
    assert f(11.5) is None
    assert f(13) is None

    p1.append((2, 1))
    assert f.is_updating is False
    assert f.domain.start == 12
    assert f.domain.end == 12
    assert not f.domain.start_open
    assert not f.domain.end_open
    assert f(12) == 3

    p1.append((3, 1))
    assert f.is_updating is False
    assert f.domain.start == 12
    assert f.domain.end == 13
    assert not f.domain.start_open
    assert not f.domain.end_open
    assert f(12) == 3
    assert f(13) == 3


def test_duplicate_function_update():
    points = Points([])
    f = points + points

    points.append((0, 1))
    assert points.is_updating is False
    assert f.is_updating is False
    assert f.domain == Interval.point(0)
    assert f.y(0) == 2

    points.append((1, 1))
    assert points.is_updating is False
    assert f.is_updating is False
    assert f.domain == Interval(0, 1)
    assert f.y(1) == 2


def test_duplicate_nested_function_update():
    points = Points([])
    f = (points + points) * 2

    points.append((0, 1))
    assert f.is_updating is False
    assert f.domain == Interval.point(0)
    assert f.y(0) == 4

    points.append((1, 1))
    assert f.is_updating is False
    assert f.domain == Interval(0, 1)
    assert f.y(1) == 4


def test_duplicate_multiple_nested_function_update():
    points = Points([])
    f = (points * 0.5 + points * 0.5) * 2

    points.append((0, 1))
    assert f.is_updating is False
    assert f.domain == Interval.point(0)
    assert f.y(0) == 2

    points.append((1, 1))
    assert f.is_updating is False
    assert f.domain == Interval(0, 1)
    assert f.y(1) == 2


# def test_duplicate_function():
#     quotes = Points()
#     jaw = quotes.close
#     teeth = quotes.close
#     ave = (jaw * 13 + teeth * 8) / 21
#     # delta = quotes.close - ave

#     mock_quotes = Quote.mock(list(np.arange(1, 25)), t_step=1)
#     for q in mock_quotes:
#         quotes.append(q)
#         assert jaw.is_updating is False
#         assert teeth.is_updating is False
#         assert ave.is_updating is False
#         # assert delta.is_updating is False
#         _ = ave.domain
#         # _ = delta.domain

#     assert ave.domain == Interval.closed(20, 27)
#     assert ave(19) is None
#     assert ave(20) is not None

#     # assert delta.domain == Interval.closed(20, 24)
#     # assert delta(19) is None
#     # assert delta(20) is not None
