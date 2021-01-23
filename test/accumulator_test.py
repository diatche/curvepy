import pytest
from curvepy.accumulator import Accumulator

def test_x():
    f = Accumulator([(1, 1), (2, 2), (3, 3)], lambda x, y, _: y)

    assert f.x_next(0) == 1
    assert f.x_next(1) == 2
    assert f.x_next(1.4) == 2
    assert f.x_next(2.6) == 3
    assert f.x_next(3) is None

    assert f.x_previous(1) is None
    assert f.x_previous(1.4) == 1
    assert f.x_previous(2.6) == 2
    assert f.x_previous(3) == 2
    assert f.x_previous(4) == 3
