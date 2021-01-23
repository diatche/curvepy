import pytest
from curvepy.generic import Generic

def test_generic():
    g = Generic(lambda x: x * 2, domain=(0, 1))
    assert g(-0.1) is None
    assert g(0) == 0
    assert g(1) == 2
    assert g(1.1) is None
    assert g.d_y(0.5) == 2