import pytest
import numpy as np
from func import Points
from . import test_util


def test_trailing_min_linear_interpolation_degree():
    f = Points(test_util.point_gen([1, 2, 3])).trailing_min(2, interpolation=0)
    assert np.allclose(f.sample_points(), [(0, 1), (1, 1), (2, 2)])
    assert f(0.5) == 1
    assert f(1) == 1
    assert f(1.5) == 1.5
    assert f(2) == 2


def test_trailing_max_linear_interpolation_degree():
    f = Points(test_util.point_gen([1, 2, 3, 2])).trailing_max(2, interpolation=0)
    assert np.allclose(f.sample_points(), [(0, 1), (1, 2), (2, 3), (3, 3)])
    assert f(0.5) == 1.5
    assert f(1) == 2
    assert f(2) == 3
    assert f(3) == 3


def test_trailing_min_previous_interpolation_degree():
    f = Points(test_util.point_gen([1, 2, 3])).trailing_min(2, interpolation=-1)
    assert np.allclose(f.sample_points(), [(0, 1), (1, 1), (2, 2)])
    assert f(0.5) == 1
    assert f(1) == 1
    assert f(1.5) == 1
    assert f(2) == 2


def test_trailing_max_previous_interpolation_degree_2():
    f = Points(test_util.point_gen([1, 2, 3, 2])).trailing_max(2, interpolation=-1)
    assert np.allclose(f.sample_points(), [(0, 1), (1, 2), (2, 3), (3, 3)])
    assert f(0.5) == 1
    assert f(1) == 2
    assert f(1.5) == 2
    assert f(2) == 3
    assert f(3) == 3


def test_trailing_max_previous_interpolation_degree_3():
    f = Points(test_util.point_gen([1, 2, 3, 2, 1, 1.5])).trailing_max(3, interpolation=-1)
    assert np.allclose(f.sample_points(), [(0, 1), (1, 2), (2, 3), (3, 3), (4, 3), (5, 2)])
    assert f(0.5) == 1
    assert f(1) == 2
    assert f(2) == 3
    assert f(3) == 3
    assert f(4) == 3
    assert f(4.5) == 3
    assert f(5) == 2


def test_trailing_min_linear_interpolation_period():
    f = Points(test_util.point_gen([1, 2, 3])).trailing_min(1, is_period=True, interpolation=0)
    assert np.allclose(f.sample_points(), [(0, 1), (1, 1), (2, 2)])
    assert f(0.5) == 1
    assert f(1) == 1
    assert f(1.5) == 1.5
    assert f(2) == 2


def test_trailing_max_linear_interpolation_period():
    f = Points(test_util.point_gen([1, 2, 3, 2])).trailing_max(1, is_period=True, interpolation=0)
    assert np.allclose(f.sample_points(), [(0, 1), (1, 2), (2, 3), (3, 3)])
    assert f(0.5) == 1.5
    assert f(1) == 2
    assert f(2) == 3
    assert f(3) == 3


def test_trailing_min_previous_interpolation_period():
    f = Points(test_util.point_gen([1, 2, 3])).trailing_min(1, is_period=True, interpolation=-1)
    assert np.allclose(f.sample_points(), [(0, 1), (1, 1), (2, 2)])
    assert f(0.5) == 1
    assert f(1) == 1
    assert f(1.5) == 1
    assert f(2) == 2


def test_trailing_max_previous_interpolation_period():
    f = Points(test_util.point_gen([1, 2, 3, 2])).trailing_max(1, is_period=True, interpolation=-1)
    assert np.allclose(f.sample_points(), [(0, 1), (1, 2), (2, 3), (3, 3)])
    assert f(0.5) == 1
    assert f(1) == 2
    assert f(2) == 3
    assert f(3) == 3
