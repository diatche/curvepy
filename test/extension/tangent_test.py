import pytest
from pytest import approx
import numpy as np
from curvepy.points import Points
from intervalpy import Interval
from .. import test_util


def test_values():
    f = Points(test_util.point_gen([2, 1, 2], t_start=10)).extension(
        'tangent', start=True, end=True)
    assert f.domain.is_negative_infinite
    assert f.domain.is_positive_infinite
    assert f(8) == 4
    assert f(9) == 3
    assert f(10) == 2
    assert f(11) == 1
    assert f(12) == 2
    assert f(13) == 3
    assert f(14) == 4


def test_internal_line_access():
    f = Points(test_util.point_gen([2, 1, 2])).extension(
        'tangent', start=True, end=True)
    f.end_func(2) == 2
    f.end_func(3) == 3


def test_values_end_only():
    f = Points(test_util.point_gen([2, 1, 2], t_start=10)).extension(
        'tangent', start=False, end=True)
    assert f.domain.start == 10
    assert f.domain.is_positive_infinite
    assert f(9) is None
    assert f(10) == 2
    assert f(11) == 1
    assert f(12) == 2
    assert f(13) == 3
    assert f(14) == 4


def test_values_start_only():
    f = Points(test_util.point_gen([2, 1, 2], t_start=10)).extension(
        'tangent', start=True, end=False)
    assert f.domain.is_negative_infinite
    assert f.domain.end == 12
    assert f(8) == 4
    assert f(9) == 3
    assert f(10) == 2
    assert f(11) == 1
    assert f(12) == 2
    assert f(13) is None


def test_empty():
    f = Points([]).extension('tangent', start=True, end=True)
    assert f(0) is None
    assert f(1) is None


def test_single_point():
    f = Points([(0, 0)]).extension('tangent', start=True, end=True)
    assert f.domain == Interval.point(0)
    assert f(0) == 0
    assert f(1) is None


def test_sample():
    f = Points(test_util.point_gen([3, 1, 2], t_start=10)).extension(
        'tangent', start=True, end=True)
    assert np.allclose(f.sample_points(domain=(10, 14)), [
                       (10, 3), (11, 1), (12, 2), (13, 3), (14, 4)])


def test_tangent_extension_big_gaps():
    f = Points(test_util.point_gen([3, 1, 2], t_step=10)).extension(
        'tangent', start=True, end=True)
    assert f(0) == 3
    assert f(10) == 1
    assert f(20) == 2
    assert f(30) == 3
    assert f(40) == 4


def test_regression_with_degree():
    noise = Points(test_util.point_gen([-0.01, 0.01] * 100, t_start=-50))
    ps = test_util.point_gen(list(reversed(range(50))) + list(range(50)), t_start=-50)
    points = Points(ps)
    assert points(0) == 0
    f = (points + noise) \
        .extension(
            'tangent',
            regression_degree=40,
            start=True,
            end=True
        )
    assert f.domain.is_negative_infinite
    assert f.domain.is_positive_infinite
    assert f(60) == approx(60, abs=2)
    assert f(-60) == approx(60, abs=2)


def test_regression_with_period():
    noise = Points(test_util.point_gen([-0.01, 0.01] * 100, t_start=-50))
    ps = test_util.point_gen(list(reversed(range(50))) + list(range(50)), t_start=-50)
    points = Points(ps)
    assert points(0) == 0
    f = (points + noise) \
        .extension(
            'tangent',
            regression_period=40,
            start=True,
            end=True
        )
    assert f.domain.is_negative_infinite
    assert f.domain.is_positive_infinite
    assert f(60) == approx(60, abs=2)
    assert f(-60) == approx(60, abs=2)


def test_update():
    points = Points(test_util.point_gen([3, 1, 2]))
    f = points.extension('tangent', start=True, end=True)
    assert f(2) == 2
    assert f(3) == 3
    points.append((3, 2))
    assert f(3) == 2


def test_update_from_empty():
    points = Points([])
    f = points.extension('tangent', start=True, end=True)
    assert f(0) is None
    points.append_list(test_util.point_gen([3, 1, 2]))
    assert f(0) == 3
    assert f(1) == 1
    assert f(2) == 2
    assert f(3) == 3
