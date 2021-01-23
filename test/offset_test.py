import pytest
import numpy as np
from func.points import Points
from pyduration import Duration
from . import test_util

HOUR = 3600.0
DAY = 86400.0


def test_offset():
    points = Points(test_util.point_gen([1, 2, 3]))

    f = points.offset(10)
    assert f.domain.start == 10
    assert f.domain.end == 12
    assert np.allclose(f.sample_points(),
                       [(10, 1), (11, 2), (12, 3)])
    assert f(10.5) == 1.5
    assert f.x_next(9.5) == 10
    assert f.x_next(10.5) == 11
    assert f.x_next(11.5) == 12
    assert f.x_next(12.5) is None
    assert f.x_previous(9.5) is None
    assert f.x_previous(10.5) == 10
    assert f.x_previous(11.5) == 11
    assert f.x_previous(12.5) == 12

    f = points.offset(0.1)
    assert f.domain.start == 0.1
    assert f.domain.end == 2.1
    assert np.allclose(f.sample_points(),
                       [(0.1, 1), (1.1, 2), (2.1, 3)])
    assert f(0.6) == 1.5
    assert f.x_next(0) == 0.1
    assert f.x_next(0.5) == 1.1
    assert f.x_next(1.5) == 2.1
    assert f.x_next(2.5) is None
    assert f.x_previous(0) is None
    assert f.x_previous(0.5) == 0.1
    assert f.x_previous(1.5) == 1.1
    assert f.x_previous(2.5) == 2.1

    f = points.offset(0)
    assert f.domain.start == 0
    assert f.domain.end == 2
    assert np.allclose(f.sample_points(), [(0, 1), (1, 2), (2, 3)])
    assert f(0.5) == 1.5
    assert f.x_next(-0.5) == 0
    assert f.x_next(0.5) == 1
    assert f.x_next(1.5) == 2
    assert f.x_next(2.5) is None
    assert f.x_previous(0) is None
    assert f.x_previous(0.5) == 0
    assert f.x_previous(1.5) == 1
    assert f.x_previous(2.5) == 2

    f = points.offset(-0.1)
    assert f.domain.start == -0.1
    assert f.domain.end == 1.9
    assert np.allclose(f.sample_points(), [
                       (-0.1, 1), (0.9, 2), (1.9, 3)])
    assert f(0.4) == 1.5
    assert f.x_next(-0.5) == -0.1
    assert f.x_next(0.5) == 0.9
    assert f.x_next(1.5) == 1.9
    assert f.x_next(2.5) is None
    assert f.x_previous(-0.5) is None
    assert f.x_previous(0.5) == -0.1
    assert f.x_previous(1.5) == 0.9
    assert f.x_previous(2.5) == 1.9

    f = points.offset(-10)
    assert f.domain.start == -10
    assert f.domain.end == -8
    assert np.allclose(f.sample_points(),
                       [(-10, 1), (-9, 2), (-8, 3)])
    assert f(-9.5) == 1.5
    assert f.x_next(-11) == -10
    assert f.x_next(-9.5) == -9
    assert f.x_next(-8.5) == -8
    assert f.x_next(-7.5) is None
    assert f.x_previous(-11) is None
    assert f.x_previous(-9.5) == -10
    assert f.x_previous(-8.5) == -9
    assert f.x_previous(-7.5) == -8


def test_offset_none():
    points = Points(test_util.point_gen([None, 1, 2]))

    f = points.offset(10)
    assert f.domain.start == 10
    assert f.domain.end == 12
    assert np.array_equal(f.sample_points(),
                          [(10, None), (11, 1), (12, 2)])


def test_offset_update():
    begin_update_count = 0
    begin_update_interval = None

    def begin_update(domain):
        nonlocal begin_update_count
        nonlocal begin_update_interval
        begin_update_count += 1
        begin_update_interval = domain

    end_update_count = 0
    end_update_interval = None

    def end_update(domain):
        nonlocal end_update_count
        nonlocal end_update_interval
        end_update_count += 1
        end_update_interval = domain

    points = Points(test_util.point_gen([1, 2, 3]))
    f = points.offset(10)
    f.add_observer(begin=begin_update, end=end_update)

    points.append((3, 4))
    assert f(13) == 4
    assert begin_update_count == 1
    assert begin_update_interval.start == 12
    assert begin_update_interval.end == 13
    assert end_update_count == 1
    assert end_update_interval.start == 12
    assert end_update_interval.end == 13


def test_multiple_nested_offset_update():
    p1 = Points([(0, 1), (1, 1)])
    p2 = Points([(2, 2), (4, 2)])

    f = (p1.offset(10) * 2 + p2.offset(10) * 2) / 2
    assert f.domain.is_empty
    assert f(10) is None
    assert f(11.5) is None
    assert f(13) is None

    p1.append((2, 1))
    assert f.domain.start == 12
    assert f.domain.end == 12
    assert not f.domain.start_open
    assert not f.domain.end_open
    assert f(12) == 3

    p1.append((3, 1))
    assert f.domain.start == 12
    assert f.domain.end == 13
    assert not f.domain.start_open
    assert not f.domain.end_open
    assert f(12) == 3
    assert f(13) == 3


def test_offset_with_duration():
    points = Points(test_util.point_gen([1, 2, 3]))

    f = points.offset(1, duration='1s')
    assert f.domain.start == 1
    assert f.domain.end == 3
    assert np.allclose(f.sample_points(),
                       [(1, 1), (2, 2), (3, 3)])
    assert f(0.5) is None
    assert f(1.4) == 1.4
    assert f(2.5) == 2.5
    assert f(3.5) is None
    assert f.x_next(0.5) == 1
    assert f.x_next(1.5) == 2
    assert f.x_next(2.5) == 3
    assert f.x_next(3.5) is None
    assert f.x_previous(0.5) is None
    assert f.x_previous(1.5) == 1
    assert f.x_previous(2.5) == 2
    assert f.x_previous(3.5) == 3

    f = points.offset(10, duration='1s')
    assert f.domain.start == 10
    assert f.domain.end == 12
    assert np.allclose(f.sample_points(),
                       [(10, 1), (11, 2), (12, 3)])
    assert f(10.5) == 1.5
    assert f.x_next(9.5) == 10
    assert f.x_next(10.5) == 11
    assert f.x_next(11.5) == 12
    assert f.x_next(12.5) is None
    assert f.x_previous(9.5) is None
    assert f.x_previous(10.5) == 10
    assert f.x_previous(11.5) == 11
    assert f.x_previous(12.5) == 12


def test_offset_with_duration_non_uniform():
    duration = Duration('20h')
    raw_points = [(ts.start, float(i + 1)) for i, ts in enumerate(duration.walk(0, limit=3))]
    assert np.allclose(raw_points, [
        (0, 1),
        (20 * HOUR, 2),
        (DAY, 3)
    ])
    points = Points(raw_points, uniform=False)

    f = points.offset(1, duration=duration)
    assert f.domain.start == 20 * HOUR
    assert f.domain.end == DAY + 20 * HOUR
    assert np.allclose(f.sample_points(), [
        (20 * HOUR, 1),
        (DAY, 2),
        (DAY + 20 * HOUR, 3)
    ])
    assert f(19 * HOUR) is None
    assert f(22 * HOUR) == 1.5
    assert f(DAY + 10 * HOUR) == 2.5
    assert f(DAY + 20.5 * HOUR) is None
    assert f.x_next(19 * HOUR) == 20 * HOUR
    assert f.x_next(22 * HOUR) == DAY
    assert f.x_next(DAY + 10 * HOUR) == DAY + 20 * HOUR
    assert f.x_next(DAY + 20.5 * HOUR) is None
    assert f.x_previous(19 * HOUR) is None
    assert f.x_previous(22 * HOUR) == 20 * HOUR
    assert f.x_previous(DAY + 10 * HOUR) == DAY
    assert f.x_previous(DAY + 20.5 * HOUR) == DAY + 20 * HOUR
