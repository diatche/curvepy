import pytest
import numpy as np
from func.extremas import Extremas
from func.constant import Constant
from func.points import Points
from . import test_util

def test_extrema():
    f = Points(test_util.point_gen([1, 3, 1, 3]))
    ref_f = Constant(2)
    e = Extremas(f, ref_f, min_step=1)
    assert np.allclose(e.sample_points(), [(0, 1), (1, 3), (2, 1)])
    assert e(0.5) == 2
    assert e(2) == 1
    assert e(2.1) is None

    f = Points(test_util.point_gen([(1), 1.1, 2.9, (3), (1), 1.1, 3]))
    ref_f = Constant(2)
    e = Extremas(f, ref_f, min_step=1)
    e_points = e.sample_points()
    assert np.allclose(e_points, [(0, 1), (3, 3), (4, 1)])
    assert e(0) == 1
    assert e(3) == 3
    assert e(3.5) == 2
    assert e(4.1) is None

def test_update_func():
    ps = Points(test_util.point_gen([1, 3, 1]))
    ref_f = Constant(2)
    e = Extremas(ps, ref_f, min_step=1)
    assert e(0) == 1
    assert e(1) == 3
    assert e(2) is None
    ps.append((3, 3))
    assert e(2) == 1
    assert e(3) is None
    ps.append((4, 1))
    assert e(3) == 3

def test_update_ref_func():
    ps = Points(test_util.point_gen([1, 3, 1.5, 3.5, 1]))
    ref_f = Constant(2)
    e = Extremas(ps, ref_f, min_step=1)
    assert np.allclose(e.sample_points(), [(0, 1), (1, 3), (2, 1.5), (3, 3.5)])
    ref_f.value = 1.25
    assert np.allclose(e.sample_points(), [(0, 1), (3, 3.5)])
