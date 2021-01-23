import pytest
import numpy as np
from func.line import Line


def test_line():
    l = Line(const=1, slope=1)
    assert l(0) == 1
    assert l(1) == 2
    assert l.d_y(0) == 1

    l = Line(p1=(0, 1), p2=(1, 2))
    assert l(0) == 1
    assert l(1) == 2
    assert l.d_y(0) == 1

    l = Line(points=[(0, 1), (1, 2)])
    assert l(0) == 1
    assert l(1) == 2
    assert l.d_y(0) == 1

    l = Line(const=1, p2=(1, 2))
    assert l(0) == 1
    assert l(1) == 2
    assert l.d_y(0) == 1

    assert np.allclose(l.sample_points(domain=(0, 2), step=1), [
                       (0, 1), (1, 2), (2, 3)])
    assert np.allclose(l.sample_points(domain=(0, 2)), [(0, 1), (2, 3)])


def test_ref_point():
    l = Line(p1=(10, 2), p2=(20, 3))
    assert l(0) == 1
    assert l(10) == 2
    assert l(15) == 2.5
    assert l(20) == 3

    l = Line(p1=(2, -10), slope=1)
    assert l(0) == -12
    assert l(2) == -10
    assert l(10) == -2
    assert l(12) == 0

    l = Line(p1=(-2, 10), slope=-2)
    assert l(-2) == 10
    assert l(0) == 6
    assert l(2) == 2


def test_partial_integration():
    l = Line(const=3, slope=5)
    assert l(3) == 18
    assert l.partial_integration(0, 3) == 31.5
