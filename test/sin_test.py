import pytest
import numpy as np
from pytest import approx
from func.sin import Sin

def test_sin():
    s = Sin(amplitude=1, period=4)
    assert s(0) == approx(0, rel=0.01)
    assert s(1) == approx(1, rel=0.01)
    assert s(2) == approx(0, rel=0.01)
    assert s(3) == approx(-1, rel=0.01)
    assert s(4) == approx(0, rel=0.01)

    assert np.allclose(s.sample_points(domain=(0, 2), min_step=1), [(0, 0), (1, 1), (2, 0)])

    s = Sin(amplitude=1, frequency=1.0/4.0)
    assert s(0) == approx(0, rel=0.01)
    assert s(1) == approx(1, rel=0.01)
    assert s(2) == approx(0, rel=0.01)
    assert s(3) == approx(-1, rel=0.01)
    assert s(4) == approx(0, rel=0.01)

    s = Sin(amplitude=1, period=4, phase_x=-1)
    assert s(0) == approx(-1, rel=0.01)
    assert s(1) == approx(0, rel=0.01)
    assert s(2) == approx(1, rel=0.01)
    assert s(3) == approx(0, rel=0.01)
    assert s(4) == approx(-1, rel=0.01)
    