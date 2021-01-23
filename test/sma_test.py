import pytest
import numpy as np
from curvepy.points import Points
from . import test_util

def test_sma_degree_1():
    f = Points(test_util.point_gen([1, 2, 3])).sma(1)
    assert np.allclose(f.sample_points(), [(0, 1), (1, 2), (2, 3)])
    assert f(0.5) == 1.5

def test_sma_degree_2():
    f = Points(test_util.point_gen([1, 2, 3, 4])).sma(2)
    assert np.allclose(f.sample_points(), [(1, 1.5), (2, 2.5), (3, 3.5)])
    assert f(1.5) == 2

def test_sma_degree_3():
    f = Points(test_util.point_gen([1, 2, 3, 4, 5, 6])).sma(3)
    assert np.allclose(f.sample_points(), [(2, 2), (3, 3), (4, 4), (5, 5)])
    assert f(2.5) == 2.5

def test_sma_degree_3_non_zero_start():
    f = Points([(2, 1), (3, 2), (4, 3), (5, 4)]).sma(3)
    assert np.allclose(f.sample_points(), [(4, 2), (5, 3)])
    assert f(4.5) == 2.5

def test_sma_degree_2_big_step():
    f = Points(test_util.point_gen([1, 2, 3, 4], t_step=10)).sma(2)
    assert np.allclose(f.sample_points(), [(10, 1.5), (20, 2.5), (30, 3.5)])
    assert f(15) == 2

def test_sma_period_1():
    f = Points(test_util.point_gen([1, 2, 3])).sma(1, is_period=True)
    assert np.allclose(f.sample_points(), [(0, 1), (1, 2), (2, 3)])
    assert f(0.5) == 1.5

def test_sma_period_2():
    f = Points(test_util.point_gen([1, 2, 3, 4])).sma(2, is_period=True)
    assert np.allclose(f.sample_points(), [(1, 1.5), (2, 2.5), (3, 3.5)])
    assert f(1.5) == 2

def test_sma_period_3():
    f = Points(test_util.point_gen([1, 2, 3, 4, 5, 6])).sma(3, is_period=True)
    assert np.allclose(f.sample_points(), [(2, 2), (3, 3), (4, 4), (5, 5)])
    assert f(2.5) == 2.5

def test_start_from_end():
    # should not calculate more info than is needed
    f = Points(test_util.point_gen([1, 2, 3, 4, 5, 6, 7, 8])).sma(3, is_period=True)
    assert f(7) == 7
    assert len(f.accumulated_points._points) == 5

def test_sample_from_end():
    f = Points(test_util.point_gen([1, 2, 3, 4, 5, 6, 7, 8, 9])).sma(3, is_period=True)
    assert np.allclose(f.sample_points(domain=(7, 8)), [(7, 7), (8, 8)])
    assert len(f.accumulated_points._points) == 6

def test_irregular_start():
    f = Points(test_util.point_gen([1, 2, 3, 4, 5, 6, 7, 8, 9])).sma(3, is_period=True)
    assert f(6.1) == 6.1
    assert f(7) == 7
    assert f(8) == 8

def test_reset_start():
    f = Points(test_util.point_gen([1, 2, 3, 4, 5, 6, 7, 8])).sma(3, is_period=True)
    assert f(6) == 6
    assert len(f.accumulated_points._points) == 5
    assert f(3) == 3
    assert len(f.accumulated_points._points) == 4
    assert f(6) == 6
    assert len(f.accumulated_points._points) == 7

def test_sma_period_20_large_step():
    f = Points(test_util.point_gen([1, 2, 3, 4], t_step=10)).sma(20, is_period=True)
    assert np.allclose(f.sample_points(), [(10, 1.5), (20, 2.5), (30, 3.5)])

def test_sma_day_period():
    f = Points(test_util.point_gen([1, 2, 3, 4], t_step=86400.0)).sma(2 * 86400.0, is_period=True)
    assert f(0) is None
    assert f(1 * 86400.0) == 1.5
    assert f(2 * 86400.0) == 2.5
    assert f(3 * 86400.0) == 3.5

def test_update_sma():
    points = Points(test_util.point_gen([1, 2, 3, 4, 5]))
    f = points.sma(2)
    assert f(4) == 4.5
    assert f(5) is None
    assert len(f.accumulated_points._points) == 3
    points.append((5, 6))
    assert f(5) == 5.5
    assert len(f.accumulated_points._points) == 4

def test_replace():
    points = Points(test_util.point_gen([1, 2, 3, 4]))
    f = points.sma(2)
    assert f(3) == 3.5
    points.replace((3, 5))
    assert f(3) == 4

def test_append_to_empty():
    points = Points([])
    sma = points.sma(2)
    points.append_list(test_util.point_gen([1, 2, 3, 4], t_start=10))
    assert np.allclose(sma.sample_points(), [(11, 1.5), (12, 2.5), (13, 3.5)])

# def test_real_data():
#     runner = db.QuoteRunner(('BTC', 'USD'), duration='day', exchange='bitstamp', update=False)
#     runner.set_date_to_now()
#     sma = runner.quote_func.close.sma(20 * 86400.0, is_period=True)
#     sma_value = sma(sma.domain.end)
#     assert True
