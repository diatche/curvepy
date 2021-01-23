import pytest
import math
import numpy as np
from pytest import approx
from func.func import Func
from func.constant import Constant
from func.points import Points
from func.line import Line
from func import Generic
from intervalpy import Interval
from . import test_util


class T:
    pass


def test_func_blend():
    c1 = Constant(2)
    c2 = Constant(3)
    b = c1.blend(c2, 4, 5)
    assert b(0) == 2
    assert b(4) == 2
    assert b(4.5) == 2.5
    assert b(5) == 3
    assert b(10) == 3


def test_func_offset_tangent_extension():
    f = Points(test_util.point_gen([2, 1, 2])).offset(
        10).extension('tangent', start=True, end=True)
    assert f.domain.is_negative_infinite
    assert f.domain.is_positive_infinite
    assert f(9) == 3
    assert f(10) == 2
    assert f(11) == 1
    assert f(12) == 2
    assert f(13) == 3
    assert f(14) == 4


def test_sample_infinite():
    f = Constant(1)
    with pytest.raises(Exception):
        f.sample_points()

    with pytest.raises(Exception):
        f.sample_points(domain=Interval.infinite())

    with pytest.raises(Exception):
        f.sample_points(domain=Interval.positive_infinite(0))

    with pytest.raises(Exception):
        f.sample_points(domain=Interval.negative_infinite(0))


def test_func_update():
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
    f = Func()
    t = f.add_observer(domain=(0, 2), begin=begin_update, end=end_update)

    f.begin_update(Interval(1, 3))
    assert begin_update_count == 1
    assert end_update_count == 0
    assert begin_update_interval.start == 1
    assert begin_update_interval.end == 3
    f.end_update(Interval(1, 3))
    assert begin_update_count == 1
    assert end_update_count == 1
    assert end_update_interval.start == 1
    assert end_update_interval.end == 3

    f.begin_update(Interval(3, 4))
    assert begin_update_count == 1
    assert end_update_count == 1
    f.end_update(Interval(3, 4))
    assert begin_update_count == 1
    assert end_update_count == 1

    f.remove_observer(t)
    f.begin_update(Interval(1, 3))
    assert begin_update_count == 1
    assert end_update_count == 1
    f.end_update(Interval(1, 3))
    assert begin_update_count == 1
    assert end_update_count == 1


def test_update_with_obj():
    begin_update_count = 0

    def begin_update(domain):
        nonlocal begin_update_count
        begin_update_count += 1

    end_update_count = 0

    def end_update(domain):
        nonlocal end_update_count
        end_update_count += 1

    f = Func()

    # Add and remove observer using object
    obj = T()
    f.add_observer(obj, begin=begin_update, end=end_update)

    f.begin_update(Interval(1, 3))
    assert begin_update_count == 1
    f.end_update(Interval(1, 3))
    assert end_update_count == 1

    f.remove_observer(obj)
    f.begin_update(Interval(1, 3))
    assert begin_update_count == 1
    f.end_update(Interval(1, 3))
    assert end_update_count == 1


def test_update_with_obj_autoremove():
    begin_update_count = 0

    def begin_update(domain):
        nonlocal begin_update_count
        begin_update_count += 1

    end_update_count = 0

    def end_update(domain):
        nonlocal end_update_count
        end_update_count += 1

    f = Func()

    # Add and remove observer using object
    obj = T()
    f.add_observer(obj, begin=begin_update, end=end_update, autoremove=True)

    f.begin_update(Interval(1, 3))
    assert begin_update_count == 1
    f.end_update(Interval(1, 3))
    assert end_update_count == 1

    obj = None
    f.begin_update(Interval(1, 3))
    assert begin_update_count == 1
    f.end_update(Interval(1, 3))
    assert end_update_count == 1


def test_min_max():
    funcs = [2, Line(const=0, slope=1)]
    minf = Func.min(funcs)
    maxf = Func.max(funcs)

    assert minf(0) == 0
    assert minf(1) == 1
    assert minf(2) == 2
    assert minf(3) == 2
    assert minf(4) == 2

    assert maxf(0) == 2
    assert maxf(1) == 2
    assert maxf(2) == 2
    assert maxf(3) == 3
    assert maxf(4) == 4


def test_first():
    funcs = [[(0, None), (1, 12), (2, None)], [(0, 1), (1, 1), (2, 1)]]
    first = Func.first(funcs)
    assert first(-1) is None
    assert first(0) == 1
    assert first(1) == 12
    assert first(2) == 1
    assert first(3) is None

    funcs = [[(0, None), (1, 12), (2, None)], 1]
    first = Func.first(funcs)
    assert first(-1) == 1
    assert first(0) == 1
    assert first(1) == 12
    assert first(2) == 1
    assert first(3) == 1

    first = Func.first([
        Generic(lambda x: 1, domain=Interval(0, 2)),
        Generic(lambda x: 2, domain=Interval.positive_infinite(1))
    ])
    assert first(-1) is None
    assert first(0) == 1
    assert first(1) == 1
    assert first(2) == 1
    assert first(2.1) == 2
    assert first(3) == 2
    assert first.sample_points(Interval(0, 3), min_step=1) == [(0, 1), (1, 1), (2, 1), (3, 2)]


def test_differential():
    assert Constant(1).differential().y(0) == 0
    assert Line(1, 2).differential().y(0) == 2
    assert Points([(0, 0), (1, 1)]).differential().y(1) == 1


def test_minimise():
    points = Points([(0, 4), (1, 3), (2, 2), (3, 1), (4, 2)])
    assert points.minimise(-0.5) is None
    assert points.minimise(0) == 3
    assert points.minimise(0.5) == 3
    assert points.minimise(1) == 3
    assert points.minimise(2) == 3
    assert points.minimise(3.1) == 3
    assert points.minimise(3) == 3
    assert points.minimise(4) == 3


def test_maximise():
    points = Points([(0, -4), (1, -3), (2, -2), (3, -1), (4, -2)])
    assert points.maximise(-0.5) is None
    assert points.maximise(0) == 3
    assert points.maximise(0.5) == 3
    assert points.maximise(1) == 3
    assert points.maximise(2) == 3
    assert points.maximise(3.1) == 3
    assert points.maximise(3) == 3
    assert points.maximise(4) == 3


def test_decorator_overloads():
    c1 = Constant(1)
    c2 = Constant(2)

    assert (c2 + 1).y(0) == 3
    assert (2 + c1).y(0) == 3
    assert (c2 - 1).y(0) == 1
    assert (2 - c1).y(0) == 1

    assert (c2 * 1).y(0) == 2
    assert (1 * c2).y(0) == 2
    assert (c2 / 4).y(0) == 0.5
    assert (1 / c2).y(0) == 0.5

    assert (-c2).y(0) == -2
    assert abs(-c2).y(0) == 2


def test_regression():
    # Get solution
    # See: https://glowingpython.blogspot.com/2012/03/linear-regression-with-numpy.html
    xi = np.arange(0, 9)
    y = [19, 20, 20.5, 21.5, 22, 23, 23, 25.5, 24]
    A = np.array([xi, np.ones(9)])
    w = np.linalg.lstsq(A.T, y, rcond=None)[0]
    slope = w[0]
    const = w[1]

    # Check implementation
    raw_points = list(zip(xi, y))
    line = Points(raw_points).regression()
    assert line.ref_point[0] == 0
    assert line.ref_point[1] == approx(const)
    assert line.slope == approx(slope)


def test_max():
    f = Func.max([Points([(0, -1), (1, 0), (2, 1)]), 0])
    assert f.domain == Interval.closed(0, 2)
    assert f.y(-1) is None
    assert f.y(0) == 0
    assert f.y(1) == 0
    assert f.y(2) == 1
    assert f.y(3) is None

    f = Func.max([0, Points([(0, -1), (1, 0), (2, 1)])])
    assert f.domain == Interval.closed(0, 2)
    assert f.y(-1) is None
    assert f.y(0) == 0
    assert f.y(1) == 0
    assert f.y(2) == 1
    assert f.y(3) is None


def test_func_parse_descriptor_line():
    f = Func.parse_descriptor({
        '$line': {
            'points': [
                [100.0, 1000.0],
                [200.0, 2000.0]
            ]
        }
    })
    assert f.y(100) == 1000.0
    assert f.y(200) == 2000.0
    assert f.y(300) == 3000.0


def test_func_parse_descriptor_add():
    f = Func.parse_descriptor({ '$add': [1, 2] })
    assert f.y(0) == 3
    f = Func.parse_descriptor({ '$add': [1, 2, 3] })
    assert f.y(0) == 6
    f = Func.parse_descriptor({ '$add': [1] })
    assert f.y(0) == 1


def test_func_parse_descriptor_max():
    f = Func.parse_descriptor({ '$max': [1, 2, 3, -1] })
    assert f.y(0) == 3


def test_func_parse_descriptor_min():
    f = Func.parse_descriptor({ '$min': [1, 2, 3, -1] })
    assert f.y(0) == -1


def test_func_parse_descriptor_args_decorator():
    f = Func.parse_descriptor({ '$add': { '@args': [10, 20] } })
    assert f.y(0) == 30


def test_func_parse_descriptor_fragment_date_decorator():
    date = Func.parse_descriptor({ '@date': '2020-02-12 01:23+1200' }, fragment=True)
    assert date == 1581427380


def test_func_parse_descriptor_log_decorator():
    f = Func.parse_descriptor({ '@log2': { '$add': [16, 16] } })
    assert f.y(0) == 256

    v = Func.parse_descriptor({ '@log10': 10 }, fragment=True)
    assert v == 10
    v = Func.parse_descriptor({ '@log': 10 }, fragment=True)
    assert v == approx(10, abs=0.01)


def test_func_parse_descriptor_constant():
    f = Func.parse_descriptor({ '$constant': 10 })
    assert f.y(0) == 10


def test_func_parse_descriptor_log():
    f = Func.parse_descriptor({ '$log': 10 })
    assert f.y(0) == approx(math.log(10), abs=0.01)
    f = Func.parse_descriptor({ '$log': { '@args': [10], 'base': 10 } })
    assert f.y(0) == 1
    f = Func.parse_descriptor({ '$log2': 16 })
    assert f.y(0) == 4


def test_func_parse_descriptor_raised():
    f = Func.parse_descriptor({ '$raised': { '@args': [4], 'base': 2 } })
    assert f.y(0) == 16


def test_func_parse_descriptor_log2():
    f = Func.parse_descriptor({ '$log2': 16 })
    assert f.y(0) == 4


def test_func_parse_descriptor_chain():
    f = Func.parse_descriptor({ '$constant': 16, '$log': { 'base': 2 } })
    assert f.y(0) == 4


def test_func_parse_descriptor_chain_with_instance_method():
    f = Func.parse_descriptor({ '$constant': -16, '$abs': [] })
    assert f.y(0) == 16


def test_func_parse_descriptor_chain_with_class_method():
    f = Func.parse_descriptor({ '$constant': 16, '$max': [10] })
    assert f.y(0) == 16


def test_func_parse_descriptor_chain_with_decorator():
    f = Func.parse_descriptor({ '@log': { '$constant': 16 }, '$max': 10 })
    assert f.y(0) == approx(16, abs=0.01)
    f = Func.parse_descriptor({ '@log': { '$constant': 16 }, '$max': [10] })
    assert f.y(0) == approx(16, abs=0.01)

    # 2 ^ (10 + 2) = 4096
    f = Func.parse_descriptor({ '@log10': { '$constant': 10 }, '@log2': { '$add': 4 } })
    assert f.y(0) == approx(4096, abs=0.01)
