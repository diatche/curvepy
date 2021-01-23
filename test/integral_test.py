import pytest
from func.constant import Constant
from func.line import Line
from func.points import Points
from . import test_util


def test_basic():
    f = Constant(1).integral(uniform=False)
    # = 1 * x + c
    assert f.domain.is_negative_infinite
    assert f.domain.is_positive_infinite
    assert f(0) == 0
    assert f(0.5) == 0.5
    assert f(1) == 1
    assert f(2) == 2
    assert f(1) == 1
    assert f(0.5) == 0.5
    assert f(0) == 0


def test_lines():
    f = Line(2, 1).integral(uniform=False)
    assert f(0) == 0
    assert f(1) == 2.5
    assert f(3) == 10.5

    f = Line(2, 1).integral(const=20, uniform=False)
    assert f(0) == 20
    assert f(1) == 22.5
    assert f(3) == 30.5

    f = Line(-2, -1).integral()
    assert f(0) == 0
    assert f(1) == -2.5

    f = Line(1, -2).integral()
    assert f(0) == 0
    assert f(0.5) == 0.25
    assert f(1) == 0


def test_points():
    f = Points([(0, 1), (1, 1), (2, 1)]).integral()
    assert f.domain.start == 0
    assert f.domain.end == 2
    assert f(-0.1) is None
    assert f(0) == 0
    assert f(0.5) == 0.5
    assert f(1) == 1
    assert f(1.5) == 1.5
    assert f(2) == 2


def test_points_non_uniform():
    f = Points([(0, 2), (1, 2), (3, 2)], uniform=False).integral(uniform=False)
    assert f.domain.start == 0
    assert f.domain.end == 3
    assert f(-0.1) is None
    assert f(0) == 0
    assert f(0.5) == 1
    assert f(1) == 2
    assert f(1.5) == 3
    assert f(2) == 4
    assert f(2.5) == 5
    assert f(3) == 6


def test_points_init_outside():
    f = Points([(1, 1), (2, 1), (3, 1)]).integral()
    assert f.domain.start == 1
    assert f.domain.end == 3
    assert f(0.9) is None
    assert f(1) == 0
    assert f(1.5) == 0.5
    assert f(2) == 1
    assert f(2.5) == 1.5
    assert f(3) == 2


def test_points_previous_interpolation():
    f = Points([(0, 2), (1, 4), (2, 6)]).integral(interpolation=Points.interpolation.previous)
    assert f.domain.start == 0
    assert f.domain.end == 2
    assert f(-0.1) is None
    assert f(0) == 0
    assert f(0.5) == 1
    assert f(1) == 2
    assert f(1.5) == 4
    assert f(2) == 6


def test_points_next_interpolation():
    f = Points([(0, 2), (1, 4), (2, 6)]).integral(interpolation=Points.interpolation.next)
    assert f.domain.start == 0
    assert f.domain.end == 2
    assert f(-0.1) is None
    assert f(0) == 0
    assert f(0.5) == 2
    assert f(1) == 4
    assert f(1.5) == 7
    assert f(2) == 10


def test_defaults():
    f = Constant(1).integral()
    assert f.domain.is_negative_infinite
    assert f.domain.is_positive_infinite
    assert f(0) == 0
    assert f(1) == 1

    f = Points(test_util.point_gen([1, 1])).integral()
    assert f.domain.start == 0
    assert f.domain.end == 1
    assert f(1) == 1


def test_none():
    f = Points([(0, None), (1, 1), (2, 2)]).integral()
    assert f.domain.start == 0
    assert f.domain.end == 2
    assert f(-0.1) is None
    assert f(0) is None
    assert f(0.5) is None
    assert f(1) == 0
    assert f(2) == 1.5


def test_updates():
    ps = Points(test_util.point_gen([1, 1, 1]))
    f = ps.integral()
    assert f(2) == 2
    ps.set([(0, 2), (1, 2), (2, 2)])
    assert f(2) == 4
