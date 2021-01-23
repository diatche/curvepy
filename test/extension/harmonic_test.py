import pytest
from func.points import Points
from .. import test_util

def test_values_end():
    f = Points(test_util.point_gen([2, 3, 1] * 10, t_start=0)).extension('harmonic', period=1, degree=4, start=False, end=True)
    assert f.domain.start == 0
    assert f.domain.is_positive_infinite
    assert f(-1) is None
    assert f(10) == 3
    assert f(11) == 1
    assert f(12) == 2
    f(20)
    # assert f(13) == 2
    # assert f(14) == 2
    return
