import pytest
import math
import numpy as np
from func.constant import Constant

def test_constant():
    c = Constant(1)
    assert c.y(0) == 1
    assert c.y(1) == 1
    assert c(0) == 1
    assert c.x(0) is None
    assert c.x(1) == 0
    assert c.d_y(0) == 0
    assert c.d_y(1) == 0
    assert c.x_next(0, min_step=1) == math.inf
    assert c.x_previous(0, min_step=1) == -math.inf
    assert c.x_next(0, min_step=1, limit=10) == 10
    assert c.x_previous(0, min_step=1, limit=-10) == -10
    assert np.allclose(c.sample_points(domain=(0, 2), step=1), [(0, 1), (1, 1), (2, 1)])
    assert np.allclose(c.sample_points(domain=(0, 2)), [(0, 1), (2, 1)])

    # updates
    f = Constant(1)
    f.value = 2
    assert f(0) == 2
