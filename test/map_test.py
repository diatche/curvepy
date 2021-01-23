import pytest
import numpy as np
from curvepy.constant import Constant
from curvepy.points import Points
from . import test_util

def test_map():
    assert Constant(1).map(lambda x, y: y * 2).y(0) == 2

    # updates
    c = Constant(1)
    f = c.map(lambda x, y: y * 2)
    c.value = 2
    assert f(0) == 4

def test_update_from_empty():
    points = Points([])
    mapped = points.map(lambda x, y: y * 2)
    assert np.array_equal(mapped.sample_points(), [])
    points.append_list(test_util.point_gen([1, 2, 3]))
    assert np.array_equal(mapped.sample_points(), [(0, 2), (1, 4), (2, 6)])

def test_get_map_during_update():
    points = Points([])
    mapped = points.map(lambda x, y: y * 2)
    callback_count = 0
    assert np.array_equal(mapped.sample_points(), [])

    def callback(*args):
        nonlocal callback_count
        callback_count += 1
        assert np.array_equal(mapped.sample_points(), [])

    points.add_observer(begin=callback)
    points.append_list(test_util.point_gen([1, 2, 3]))
    assert callback_count == 1

def test_get_map_after_update():
    points = Points([])
    mapped = points.map(lambda x, y: y * 2)
    callback_count = 0
    assert np.array_equal(mapped.sample_points(), [])

    def callback(*args):
        nonlocal callback_count
        callback_count += 1
        assert np.array_equal(mapped.sample_points(), [(0, 2), (1, 4), (2, 6)])

    points.add_observer(end=callback)
    points.append_list(test_util.point_gen([1, 2, 3]))
    assert callback_count == 1

def test_get_map_after_update_observer_before_map():
    # Add an observer before mapping
    callback_count = 0
    mapped = None

    def callback(*args):
        nonlocal callback_count
        callback_count += 1
        assert np.array_equal(mapped.sample_points(), [(0, 2), (1, 4), (2, 6)])

    points = Points([])
    points.add_observer(end=callback)
    mapped = points.map(lambda x, y: y * 2)
    assert np.array_equal(mapped.sample_points(), [])

    points.append_list(test_util.point_gen([1, 2, 3]))
    assert callback_count == 1
