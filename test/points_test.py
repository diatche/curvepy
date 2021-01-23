import pytest
import numpy as np
from pytest import approx
from curvepy.points import Points
from intervalpy import Interval
from . import test_util


def test_step():
    ps = Points(test_util.point_gen([1, 2, 3], t_start=1))

    assert ps.x_next(-1, min_step=1e-5) == 1
    assert ps.x_next(0.9, min_step=1e-5) == 1
    assert ps.x_next(1, min_step=1e-5) == 2
    assert ps.x_next(1, min_step=1) == 2
    assert ps.x_next(1, min_step=1.5) == 3
    assert ps.x_next(2, min_step=1e-5) == 3
    assert ps.x_next(2, min_step=1) == 3
    assert ps.x_next(2, min_step=1.5) is None
    assert ps.x_next(4, min_step=1.5) is None

    assert ps.x_previous(5, min_step=1e-5) == 3
    assert ps.x_previous(4.1, min_step=1e-5) == 3
    assert ps.x_previous(4, min_step=1e-5) == 3
    assert ps.x_previous(4, min_step=1) == 3
    assert ps.x_previous(4, min_step=1.5) == 2
    assert ps.x_previous(2, min_step=1e-5) == 1
    assert ps.x_previous(2, min_step=1) == 1
    assert ps.x_previous(2, min_step=1.5) == None
    assert ps.x_previous(0, min_step=1.5) == None


def test_linear_interpolation():
    ps = Points(test_util.point_gen(
        [1, 2, 3], t_start=1), interpolation=Points.interpolation.linear)
    assert ps.domain.start == 1
    assert ps.domain.end == 3
    assert ps(1) == 1
    assert ps(1.5) == approx(1.5, rel=0.01)
    assert ps(2) == 2
    assert ps(3) == 3
    assert ps(3.1) is None
    assert ps(0.9) is None


def test_previous_interpolation():
    ps = Points(test_util.point_gen(
        [1, 2, 3], t_start=1), interpolation=Points.interpolation.previous)
    assert ps(1) == 1
    assert ps(1.5) == 1
    assert ps(3) == 3
    assert ps(3.1) is None
    assert ps(0.9) is None


def test_next_interpolation():
    ps = Points(test_util.point_gen(
        [1, 2, 3], t_start=1), interpolation=Points.interpolation.next)
    assert ps(1) == 1
    assert ps(1.5) == 2
    assert ps(3) == 3
    assert ps(3.1) is None
    assert ps(0.9) is None


def test_sample():
    ps = Points(test_util.point_gen([1, 2, 3], t_start=1))

    assert np.allclose(ps.sample_points(
        domain=(1, 3), min_step=1e-5), [(1, 1), (2, 2), (3, 3)])
    assert np.allclose(ps.sample_points(
        domain=(1, 3), min_step=1), [(1, 1), (2, 2), (3, 3)])
    assert np.allclose(ps.sample_points(
        domain=(1, 3), min_step=1.5), [(1, 1), (3, 3)])
    assert np.allclose(ps.sample_points(domain=(1, 3), step=0.5), [
                       (1, 1), (1.5, 1.5), (2, 2), (2.5, 2.5), (3, 3)])
    assert np.allclose(ps.sample_points(
        domain=(1, 2), step=1), [(1, 1), (2, 2)])
    assert np.allclose(ps.sample_points(step=1), [(1, 1), (2, 2), (3, 3)])


def test_missing_points():
    points = test_util.point_gen([1, 2, 3] * 10)
    del points[8]
    with pytest.raises(Exception):
        Points(points, uniform=True)

    points = test_util.point_gen([1, 3, 3, 4])
    del points[1]
    ps = Points(points, uniform=False)
    assert not ps.is_uniform
    assert ps(0) == 1
    assert ps(0.5) == 1.5
    assert ps(1) == 2
    assert ps(1.5) == 2.5
    assert ps(2) == 3
    assert ps(2.5) == 3.5
    assert ps(3) == 4


def test_update():
    ps = Points([(0, 1), (1, 2)])
    assert ps.is_updating is False
    assert ps(2) is None
    ps.append((2, 3))
    assert ps.is_updating is False
    assert ps(2) == 3


def test_update_from_empty():
    ps = Points([])
    assert ps(0) is None

    ps.append((0, 1))
    assert ps.is_updating is False
    assert ps(0) == 1

    ps.append((1, 2))
    assert ps.is_updating is False
    assert ps(1) == 2

    ps.append((2, 3))
    assert ps.is_updating is False
    assert ps(2) == 3


def test_update_equally_spaced_with_non_equally_spaced():
    points = Points([(0, 1), (1, 2)], uniform=False)
    assert points.is_uniform
    points.append((3, 4))
    assert not points.is_uniform
    assert points(0) == 1
    assert points(1) == 2
    assert points(2) == 3
    assert points(3) == 4
    assert np.array_equal(points.sample_points(), [(0, 1), (1, 2), (3, 4)])
    assert np.array_equal(points.sample_points(step=1), [
                          (0, 1), (1, 2), (2, 3), (3, 4)])


def test_replace():
    points = Points([(0, 1), (1, 2)], uniform=False)
    assert points(1) == 2
    points.replace((1, 3))
    assert points(1) == 3

    points = Points([(0, 1), (1, 2)], uniform=False)
    assert points(0.5) == 1.5
    points.replace((0.5, 3))
    assert points(0.5) == 3

    points = Points([(0, 1), (1, 2)], uniform=True)
    with pytest.raises(Exception):
        points.replace((0.5, 3))

    points = Points([(0, 1), (1, 2)], uniform=False)
    assert points(2) is None
    with pytest.raises(Exception):
        points.replace((2, 3), or_append=False)
    points.replace((2, 3), or_append=True)
    assert points(2) == 3


def test_reset():
    update_interval = None

    def did_update(domain):
        nonlocal update_interval
        update_interval = domain

    points = [(0, 1), (1, 2), (2, 3)]
    pf = Points(points, uniform=False)
    pf.reset()
    assert pf.domain.is_empty

    pf = Points(points, uniform=False)
    update_interval = None
    pf.add_observer(end=did_update)
    assert pf(1) == 2
    assert pf(2) == 3
    pf.reset((2, 2))
    assert pf(1) == 2
    assert pf(2) is None
    assert update_interval.start == 1
    assert update_interval.start_open
    assert update_interval.end == 2
    assert not update_interval.end_open

    pf = Points(points, uniform=False)
    update_interval = None
    pf.add_observer(end=did_update)
    assert pf(0) == 1
    assert pf(1) == 2
    assert pf(2) == 3
    pf.reset((1, 1))
    assert pf(0) == 1
    assert pf(1) == 2
    assert pf(2) == 3
    assert update_interval.start == 0
    assert update_interval.start_open
    assert update_interval.end == 2
    assert update_interval.end_open

    pf = Points(points, uniform=True)
    with pytest.raises(Exception):
        pf.reset((1, 1))


def test_reset_closed_interval():
    points = [(0, 1), (1, 5), (2, 3), (3, 4)]
    pf = Points(points, uniform=False)
    assert pf(1) == 5
    pf.reset(domain=Interval.closed(1, 2))
    assert pf(1) == 2


def test_reset_open_interval():
    points = [(0, 1), (1, 5), (2, 3)]
    pf = Points(points, uniform=False)
    assert pf(1) == 5
    pf.reset(domain=Interval.open(0, 2))
    assert pf(0) == 1
    assert pf(1) == 2
    assert pf(2) == 3


def test_interval_indexes():
    points = Points([(0, 0), (1, 1), (2, 2), (3, 3)])

    i0, i1 = points._domain_indexes(Interval.closed(-2, -1))
    assert i0 == i1

    i0, i1 = points._domain_indexes(Interval.closed(-2, 0))
    assert i0 == 0
    assert i1 == 1

    i0, i1 = points._domain_indexes(Interval.open(-2, 0))
    assert i0 == i1

    i0, i1 = points._domain_indexes(Interval.closed(0, 0))
    assert i0 == 0
    assert i1 == 1

    i0, i1 = points._domain_indexes(Interval.open(0, 1))
    assert i0 == i1

    i0, i1 = points._domain_indexes(Interval.closed(0, 1))
    assert i0 == 0
    assert i1 == 2

    i0, i1 = points._domain_indexes(Interval.closed(2, 3))
    assert i0 == 2
    assert i1 == 4

    i0, i1 = points._domain_indexes(Interval.open(2, 3))
    assert i0 == 3
    assert i1 == 3

    i0, i1 = points._domain_indexes(Interval.closed(3, 3))
    assert i0 == 3
    assert i1 == 4

    i0, i1 = points._domain_indexes(Interval.open(3, 3))
    assert i0 == i1

    i0, i1 = points._domain_indexes(Interval.closed(3, 4))
    assert i0 == 3
    assert i1 == 4

    i0, i1 = points._domain_indexes(Interval.open(3, 4))
    assert i0 == i1
