import pytest
import numpy as np
from func.points import Points
from .. import test_util

def test_values():
    f = Points(test_util.point_gen([3, 1, 2], t_start=10)).extension('constant', start=True, end=True)
    assert f.domain.is_negative_infinite
    assert f.domain.is_positive_infinite
    assert f(8) == 3
    assert f(9) == 3
    assert f(10) == 3
    assert f(11) == 1
    assert f(12) == 2
    assert f(13) == 2
    assert f(14) == 2

def test_values_end_only():
    f = Points(test_util.point_gen([3, 1, 2], t_start=10)).extension('constant', start=False, end=True)
    assert f.domain.start == 10
    assert f.domain.is_positive_infinite
    assert f(9) is None
    assert f(10) == 3
    assert f(11) == 1
    assert f(12) == 2
    assert f(13) == 2
    assert f(14) == 2

def test_values_start_only():
    f = Points(test_util.point_gen([3, 1, 2], t_start=10)).extension('constant', start=True, end=False)
    assert f.domain.is_negative_infinite
    assert f.domain.end == 12
    assert f(8) == 3
    assert f(9) == 3
    assert f(10) == 3
    assert f(11) == 1
    assert f(12) == 2
    assert f(13) is None

def test_empty():
    f = Points([]).extension('constant', start=True, end=True)
    assert f(0) is None
    assert f(1) is None

def test_single_point():
    f = Points([(0, 0)]).extension('constant', start=True, end=True)
    assert f(-1) == 0
    assert f(0) == 0
    assert f(1) == 0

def test_sample():
    f = Points(test_util.point_gen([3, 1, 2], t_start=10)).extension('constant', start=True, end=True)
    assert np.allclose(f.sample_points(domain=(10, 14)), [(10, 3), (11, 1), (12, 2), (13, 2), (14, 2)])

def test_update():
    points = Points(test_util.point_gen([3, 1, 2]))
    f = points.extension('constant', start=True, end=True)
    assert f(2) == 2
    assert f(3) == 2
    points.append((3, 5))
    assert f(3) == 5

def test_update_from_empty():
    points = Points([])
    f = points.extension('constant', start=True, end=True)
    assert f(0) is None
    points.append_list(test_util.point_gen([3, 1, 2]))
    assert f(0) == 3
    assert f(1) == 1
    assert f(2) == 2
    assert f(3) == 2
