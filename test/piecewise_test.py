import pytest
import numpy as np
from curvepy.piecewise import Piecewise
from curvepy.constant import Constant
from curvepy.points import Points
from intervalpy import Interval
from . import test_util

def test_constant_step():
    c1 = Constant(2)
    c2 = Constant(3)
    ds = Interval(0, 3).partition([2])
    pw = Piecewise([c1, c2], ds)
    assert pw.domain.start == 0
    assert pw.domain.end == 3
    assert pw(-0.1) is None
    assert pw(0) == 2
    assert pw(1.9) == 2
    assert pw(2) == 3
    assert pw(3) == 3
    assert pw(3.1) is None
    assert np.allclose(pw.sample_points(domain=(0, 3), step=1), [(0, 2), (1, 2), (2, 3), (3, 3)])
    # assert np.allclose(pw.sample_points(domain=(0, 3)), [(0, 2), (2, 3), (3, 3)])

def test_varying_step():
    c1 = Constant(2)
    c2 = Points(test_util.point_gen([3, 4], t_start=2))
    ds = Interval(1, 3).partition([2])
    pw = Piecewise([c1, c2], ds)
    assert pw.domain.start == 1
    assert pw.domain.end == 3
    assert pw(0.9) is None
    assert pw(1) == 2
    assert pw(1.9) == 2
    assert pw(2) == 3
    assert pw(3) == 4
    assert pw(3.1) is None
    assert np.allclose(pw.sample_points(domain=(0, 3), step=0.5), [(1, 2), (1.5, 2), (2, 3), (2.5, 3.5), (3, 4)])
    # assert np.allclose(pw.sample_points(domain=(0, 3), min_step=0.5), [(1, 2), (2, 3), (3, 4)])
