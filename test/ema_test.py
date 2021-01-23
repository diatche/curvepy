import pytest
import numpy as np
from pytest import approx
from curvepy.points import Points
from . import test_util

def test_ema_alpha():
    f = Points(test_util.point_gen([1, 2, 1, 2])).ema(0.5, is_period=False)
    assert f(0) == 1
    assert f(1) == approx(1.5, abs=0.01)
    assert f(2) == approx(1.25, abs=0.01)
    assert f(3) == approx((1.25 + 2.0) * 0.5, abs=0.01)
    assert np.allclose(f.sample_points(), [(0, 1), (1, 1.5), (2, 1.25), (3, (1.25 + 2.0) * 0.5)])
    assert np.allclose(f.sample_points(step=2), [(0, 1), (2, 1.25)])

    f = Points(test_util.point_gen([1, 2, 1, 2])).ema(0.25, is_period=False)
    assert f(0) == 1
    assert f(1) == approx(0.75 + 2 * 0.25, abs=0.01)
    assert f(2) == approx((0.75 + 2 * 0.25) * 0.75 + 1 * 0.25, abs=0.01)
    assert f(3) == approx(((0.75 + 2 * 0.25) * 0.75 + 1 * 0.25) * 0.75 + 2 * 0.25, abs=0.01)

def test_ema_period():
    f = Points(test_util.point_gen([1, 2, 1, 2])).ema(2, is_period=True)
    assert f(1) == approx(1.5, abs=0.01)

def test_update_ema():
    points = Points(test_util.point_gen([1, 2, 1]))
    f = points.ema(0.5, is_period=False)
    assert f(3) is None
    points.append((3, 2))
    assert f(3) == approx((1.25 + 2.0) * 0.5, abs=0.01)

def test_update_ema_from_empty():
    points = Points([])
    f = points.ema(0.5, is_period=False)
    points.append_list(test_util.point_gen([1, 2, 1]))
    assert np.allclose(f.sample_points(), [(0, 1), (1, 1.5), (2, 1.25)])

def test_update_ema_from_empty_non_zero_start():
    points = Points([])
    f = points.ema(0.5, is_period=False)
    points.append_list([(1, 1), (2, 2), (3, 1)])
    assert np.allclose(f.sample_points(), [(1, 1), (2, 1.5), (3, 1.25)])

# def test_ema_irregular():
#     f = Points(test_util.point_gen([1, 2, 1, 2])).ema(3, is_period=True)
#     assert f(0) == 1
#     assert f(1) == approx(1.15, abs=0.01)
#     assert f(2) == approx(1.24, abs=0.01)
#     assert f(3) == approx(1.32, abs=0.01)
#     assert np.allclose(f.sample_points(), [(0, 1), (1, 1.15), (2, 1.24), (3, 1.32)], rtol=0.01)

# def test_update_ema_irregular_from_empty():
#     points = Points([])
#     f = points.ema(3, is_period=True)
#     points.append_list(test_util.point_gen([1, 2, 1]))
#     assert np.allclose(f.sample_points(), [(0, 1), (1, 1.15), (2, 1.24)], rtol=0.01)

# def test_update_ema_irregular_from_empty_non_zero_start():
#     points = Points([])
#     f = points.ema(3, is_period=True)
#     points.append_list([(2, 1), (3, 2), (4, 1)])
#     assert np.allclose(f.sample_points(), [(2, 1), (3, 1.15), (4, 1.24)], rtol=0.01)
