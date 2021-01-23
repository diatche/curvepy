import pytest
import numpy as np

# def test_straight_line():
#     ps = Points(test_util.point_gen([1, 1, 1]))
#     trend = Trend(ps, 2)

#     lines = trend(0)
#     assert len(lines) == 2
#     assert np.allclose(list(lines[0]), [(0, 1), (2, 1)])
#     assert len(lines[0].intersections) == 0
#     assert np.allclose(list(lines[1]), [(0, 1), (2, 1)])
#     assert len(lines[1].intersections) == 0

#     assert np.allclose(list(trend(2)), [(0, 1), (2, 1)])
#     assert np.allclose(list(trend(3)), [(0, 1), (2, 1)])

# def test_trend_basic():
#     ps = Points(test_util.point_gen([1, 3, 2, 4, 3, 5, 4, 6]))
#     trend = Trend(ps, 3)

#     lines = trend(0)
#     assert len(lines) == 1
#     assert lines[0].is_lower_trend
#     assert np.allclose(list(lines[0]), [(0, 1), (6, 4)])
#     assert len(lines[0].intersections) == 0

#     lines = trend(1)
#     assert len(lines) == 2
#     assert np.allclose(list(lines[0]), [(0, 1), (6, 4)])
#     assert np.allclose(list(lines[1]), [(1, 3), (7, 6)])
#     assert len(lines[1].intersections) == 0

# def test_trend_intersection_1():
#     ps = Points(test_util.point_gen([2, 2, 2, 1, 3]))
#     trend = Trend(ps, 2)
#     lines = trend(0)
#     assert np.allclose(lines, [[(0, 2), (2, 2)]])
#     assert np.allclose(lines[0].intersections, [(3.5, 2)])
#     assert np.allclose(lines[0].line_extended(intersection_index=0), [(0, 2), (3.5, 2)])

# def test_trend_intersection_2():
#     ps = Points(test_util.point_gen([2, 1, 2, 1, 2, 1, 3]))
#     trend = Trend(ps, 4)
#     lines = trend(0)
#     assert np.allclose(lines, [[(0, 2), (4, 2)]])
#     assert np.allclose(lines[0].intersections, [(5.5, 2)])
#     assert np.allclose(lines[0].line_extended(intersection_index=0), [(0, 2), (5.5, 2)])

# def test_trend_double_intersection():
#     ps = Points(test_util.point_gen([2, 2, 2, 1, 3, 1]))
#     trend = Trend(ps, 2)
#     line = trend(0)[0]
#     assert np.allclose(line.intersections, [(3.5, 2), (4.5, 2)])
#     assert np.allclose(line.line_extended(intersection_index=0), [(0, 2), (3.5, 2)])
#     assert np.allclose(line.line_extended(intersection_index=1), [(0, 2), (4.5, 2)])
#     assert np.allclose(line.line_extended(intersection_index=-1), [(0, 2), (4.5, 2)])

# def test_trend_tangent_points_1():
#     ps = Points(test_util.point_gen([2, 2, 2, 1, 3, 2, 3]))
#     trend = Trend(ps, 2)
#     line = trend(0)[0]
#     # When there are multiple equidistant adjacent tangents points, the first one is picked
#     assert np.allclose(line.tangent_points, [(0, 2), (5, 2)])

# def test_trend_tangent_points_2():
#     ps = Points(test_util.point_gen([1, 2, 2, 2, 1, 3, 2, 3]))
#     trend = Trend(ps, 2)
#     line = trend(1)[0]
#     # When there are multiple equidistant adjacent tangents points, the first one is picked
#     assert np.allclose(line.tangent_points, [(1, 2), (6, 2)])

# def test_trend_tangent_points_3():
#     ps = Points(test_util.point_gen([2, 1, 2, 1, 2, 1, 3, 2, 3]))
#     trend = Trend(ps, 4)
#     line = trend(0)[0]
#     assert np.allclose(line.tangent_points, [(0, 2), (2, 2), (4, 2), (7, 2)])

# def test_trend_extremas_1():
#     ps = Points(test_util.point_gen([2, 2, 2, 1, 3.1, 2.5, 3.3]))
#     trend = Trend(ps, 2)
#     line = trend(0)[0]
#     assert np.allclose(line.extremas, [(3, 1), (6, 3.3)])

# def test_trend_extremas_2():
#     ps = Points(test_util.point_gen([1, 2, 2, 2, 1, 3.1, 2.5, 3.3]))
#     trend = Trend(ps, 2)
#     line = trend(1)[0]
#     assert np.allclose(line.extremas, [(0, 1), (4, 1), (7, 3.3)])

# def test_trend_extremas_3():
#     ps = Points(test_util.point_gen([2, 1, 2, 0.9, 2, 1, 3.1, 2, 3.3]))
#     trend = Trend(ps, 4)
#     line = trend(0)[0]
#     assert np.allclose(line.extremas, [(1, 1), (3, 0.9), (5, 1), (6, 3.1), (8, 3.3)])

# def test_trend_extremas_4():
#     ps = Points(test_util.point_gen([2, 1, 2, 0.9, 2, 1, 3.1, 2.5, 3.3]))
#     trend = Trend(ps, 4)
#     line = trend(0)[0]
#     assert np.allclose(line.extremas, [(1, 1), (3, 0.9), (5, 1), (8, 3.3)])

# def test_trend_extremas_5():
#     ps = Points(test_util.point_gen([2, 1, 2, 0.9, 2, 1, 3.3, 2.5, 3.1]))
#     trend = Trend(ps, 4)
#     line = trend(0)[0]
#     assert np.allclose(line.extremas, [(1, 1), (3, 0.9), (5, 1), (6, 3.3)]) 

# def test_trend_prediction_intersect_retest_fulfill():
#     ps = Points(test_util.point_gen([2, 1, 2, 1, 2, 1, 3, 2, 5]))
#     trend = Trend(ps, 2)
#     line = trend.upper(0)[0]
#     assert np.allclose(line.prediction_origin, (0, 2))
#     assert np.allclose(line.prediction_intersection, (5.5, 2))
#     assert np.allclose(line.prediction_extrema, (6, 3))
#     assert np.allclose(line.prediction_retest_point, (7, 2))
#     assert np.allclose(line.prediction_confirmation_line, [(0, 2), (6, 3)])
#     assert line.prediction_y == approx(2 + test_util.GOLD_2)
#     assert line.prediction_succeeded
#     assert not line.prediction_failed
#     assert line.prediction_phase == TrendLine.PREDICTION_PHASE_FULFILLED
#     assert np.allclose(line.prediction_success_point, (8, 5))

# def test_trend_prediction_intersect_retest_confirm_fulfill():
#     ps = Points(test_util.point_gen([2, 1, 2, 1, 2, 1, 3, 2, 4, 5]))
#     trend = Trend(ps, 4)
#     line = trend.upper(0)[0]
#     assert np.allclose(line.prediction_origin, (0, 2))
#     assert np.allclose(line.prediction_intersection, (5.5, 2))
#     assert np.allclose(line.prediction_extrema, (6, 3))
#     assert np.allclose(line.prediction_retest_point, (7, 2))
#     assert np.allclose(line.prediction_confirmation_line, [(0, 2), (6, 3)])
#     assert line.prediction_y == approx(2 + test_util.GOLD_2)
#     assert line.prediction_succeeded
#     assert not line.prediction_failed
#     assert line.prediction_phase == TrendLine.PREDICTION_PHASE_FULFILLED
#     assert np.allclose(line.prediction_success_point, (9, 5))

# def test_trend_prediction_intersect_retest_retest_confirm_fulfill():
#     # TODO: Should the prediction be based on the first or last or highest extrema? Assuming last for now.
#     ps = Points(test_util.point_gen([2, 1, 1, 2, 1, 2, 1, 3, 2, 2.5, 2, 5]))
#     trend = Trend(ps, 4)
#     line = trend.upper(0)[0]
#     assert np.allclose(line.prediction_origin, (0, 2))
#     assert np.allclose(line.prediction_intersection, (6.5, 2))
#     assert np.allclose(line.prediction_extrema, (9, 2.5))
#     assert np.allclose(line.prediction_retest_point, (10, 2))
#     assert np.allclose(line.prediction_confirmation_line, [(0, 2), (9, 2.5)])
#     assert line.prediction_y == approx(2 + test_util.GOLD_2 * (2.5 - 2))
#     assert line.prediction_succeeded
#     assert not line.prediction_failed
#     assert line.prediction_phase == TrendLine.PREDICTION_PHASE_FULFILLED
#     assert np.allclose(line.prediction_success_point, (11, 5))

# def test_trend_prediction_intersect_retest_confirm_retest_confirm_fulfill():
#     ps = Points(test_util.point_gen([2, 1, 1, 2, 1, 2, 1, 3, 2, 3.1, 2, 5]))
#     trend = Trend(ps, 2)
#     line = trend.upper(0)[0]
#     assert np.allclose(line.prediction_origin, (0, 2))
#     assert np.allclose(line.prediction_intersection, (6.5, 2))
#     assert np.allclose(line.prediction_extrema, (9, 3.1))
#     assert np.allclose(line.prediction_retest_point, (10, 2))
#     assert np.allclose(line.prediction_confirmation_line, [(0, 2), (9, 3.1)])
#     assert line.prediction_y == approx(2 + test_util.GOLD_2 * (3.1 - 2))
#     assert line.prediction_succeeded
#     assert not line.prediction_failed
#     assert line.prediction_phase == TrendLine.PREDICTION_PHASE_FULFILLED
#     assert np.allclose(line.prediction_success_point, (11, 5))

# def test_trend_prediction_intersect_retest_confirm_fail():
#     ps = Points(test_util.point_gen([2, 1, 2, 1, 2, 1, 3, 2, 4, 1]))
#     trend = Trend(ps, 2)
#     line = trend.upper(0)[0]
#     assert np.allclose(line.prediction_origin, (0, 2))
#     assert np.allclose(line.prediction_intersection, (5.5, 2))
#     assert np.allclose(line.prediction_extrema, (6, 3))
#     assert np.allclose(line.prediction_retest_point, (7, 2))
#     assert np.allclose(line.prediction_confirmation_line, [(0, 2), (6, 3)])
#     assert line.prediction_y == approx(2 + test_util.GOLD_2)
#     assert not line.prediction_succeeded
#     assert line.prediction_failed
#     assert line.prediction_phase == TrendLine.PREDICTION_PHASE_CONFIRMED

# def test_trend_prediction_intersect_fail():
#     ps = Points(test_util.point_gen([2, 1, 2, 1, 2, 1, 3, 1]))
#     trend = Trend(ps, 2)
#     line = trend.upper(0)[0]
#     assert np.allclose(line.prediction_origin, (0, 2))
#     assert np.allclose(line.prediction_intersection, (5.5, 2))
#     assert np.allclose(line.prediction_extrema, (6, 3))
#     assert line.prediction_retest_point is None
#     assert np.allclose(line.prediction_confirmation_line, [(0, 2), (6, 3)])
#     assert line.prediction_y == approx(2 + test_util.GOLD_2)
#     assert not line.prediction_succeeded
#     assert line.prediction_failed
#     assert line.prediction_phase == TrendLine.PREDICTION_PHASE_INTERSECTED

# def test_trend_prediction_intersect_timeout():
#     ps = Points(test_util.point_gen([2, 1, 2, 1, 2, 1, 3, 2.5, 2.3, 2, 5]))
#     trend = Trend(ps, 2)
#     line = trend.upper(0)[0]
#     assert np.allclose(line.prediction_origin, (0, 2))
#     assert np.allclose(line.prediction_intersection, (5.5, 2))
#     assert np.allclose(line.prediction_extrema, (6, 3))
#     assert line.prediction_retest_point is None
#     assert np.allclose(line.prediction_confirmation_line, [(0, 2), (6, 3)])
#     assert line.prediction_y == approx(2 + test_util.GOLD_2)
#     assert not line.prediction_succeeded
#     assert line.prediction_failed
#     assert line.prediction_phase == TrendLine.PREDICTION_PHASE_INTERSECTED

# def test_trend_basic_with_gaps():
#     ps = Points(test_util.point_gen([(1), 2, (3), 2.5, (2), 3, (4), 3.5, (3), 4, (5), 4.5, (4), 5, (6)]))
#     trend = Trend(ps, 3)

#     lines = trend(0)
#     assert len(lines) == 1
#     assert np.allclose(list(lines[0]), [(0, 1), (12, 4)])
#     assert len(lines[0].intersections) == 0

#     lines = trend(2)
#     assert len(lines) == 2
#     assert np.allclose(list(lines[0]), [(0, 1), (12, 4)])
#     assert np.allclose(list(lines[1]), [(2, 3), (14, 6)])
#     assert len(lines[1].intersections) == 0

# def test_trend_with_unrelated_noise():
#     ps = Points(test_util.point_gen([(1), 2.12312, (3), 2.5834, (2), 3.123, (4), 3.534, (3), 4.17534, (5), 4.59764, (4), 5.1232, (6)]))
#     trend = Trend(ps, 3)
    
#     lines = trend(0)
#     assert len(lines) == 1
#     assert np.allclose(list(lines[0]), [(0, 1), (12, 4)])
#     assert len(lines[0].intersections) == 0

#     lines = trend(2)
#     assert len(lines) == 2
#     assert np.allclose(list(lines[0]), [(0, 1), (12, 4)])
#     assert np.allclose(list(lines[1]), [(2, 3), (14, 6)])
#     assert len(lines[1].intersections) == 0

# def test_trend_with_trend_noise():
#     ps = Points(test_util.point_gen([1.0123, 3.0234, 2.02312, 4.03434, 3.02323, 5.04234, 4.0121, 6.0123]))
#     trend = Trend(ps, 3, x_tol_rel=0.05, y_tol_rel=0.05)

#     lines = trend(0)
#     assert len(lines) == 1
#     assert np.allclose(list(lines[0]), [(0, 1), (6, 4)], rtol=0.05)
#     assert len(lines[0].intersections) == 0

#     lines = trend(1)
#     assert len(lines) == 2
#     assert np.allclose(list(lines[0]), [(0, 1), (6, 4)], rtol=0.05)
#     assert np.allclose(list(lines[1]), [(1, 3), (7, 6)], rtol=0.05)
#     assert len(lines[1].intersections) == 0

# def test_larger_trends():
#     ps = Points(test_util.point_gen([1, 2, 1, 2, 1, 2, 1, 3, 2, 3, 2, 3, 2, 4, 3, 4, 3, 4, 3]))
#     trend = Trend(ps, 2)

#     upper = trend.upper(6)
#     assert len(upper) == 2
#     assert np.allclose(list(upper[0]), [(1, 2), (12, 2)])
#     assert np.allclose(list(upper[1]), [(1, 2), (13, 4)])
#     assert np.allclose(upper[0].intersections, [(6.5, 2)])
#     assert len(upper[1].intersections) == 0

#     lower = trend.lower(6)
#     assert np.allclose(list(lower[0]), [(0, 1), (6, 1)])
#     assert np.allclose(list(lower[1]), [(6, 1), (18, 3)])
#     assert len(lower[0].intersections) == 0
#     assert len(lower[1].intersections) == 0

# def test_trend_update():
#     ps = Points(test_util.point_gen([1, 1, 1]))
#     trend = Trend(ps, 2)
#     lines = trend(0)
#     assert np.allclose(lines, [[(0, 1), (2, 1)]], rtol=0.01)
#     ps.set([(0, 2), (1, 2), (2, 2)])
#     lines = trend(0)
#     assert np.allclose(lines, [[(0, 2), (2, 2)]], rtol=0.01)

# def test_trend_update_intersection():
#     ps = Points(test_util.point_gen([2, 2, 2, 1, 3]))
#     trend = Trend(ps, 2)
#     _ = trend(0)
#     ps.set([(0, 2), (1, 2), (2, 2), (3, 2), (4, 2)])
#     lines = trend(0)
#     assert len(lines[0].intersections) == 0
#     ps.set([(0, 2), (1, 2), (2, 2), (3, 1), (4, 3)])
#     lines = trend(0)
#     assert np.allclose(lines[0].intersections, [(3.5, 2)], rtol=0.01)

# def test_trend_update_trend_points():
#     ps = Points(test_util.point_gen([2, 2, 2, 1, 3, 2, 3]))
#     trend = Trend(ps, 2)
#     _ = trend(0)
#     ps.set([(0, 2), (1, 2), (2, 2), (3, 2), (4, 2), (5, 2), (6, 2)])
#     line = trend(0)[0]
#     # When there are multiple equidistant adjacent tangents points, the first one is picked
#     assert np.allclose(line.tangent_points, [(0, 2)])
#     ps.set([(0, 2), (1, 2), (2, 2), (3, 1), (4, 3), (5, 2), (6, 3)])
#     line = trend(0)[0]
#     assert np.allclose(line.tangent_points, [(0, 2), (5, 2)])

# def test_trend_update_extremas():
#     ps = Points(test_util.point_gen([2, 2, 2, 1, 3.1, 2.5, 3.3]))
#     trend = Trend(ps, 2)
#     _ = trend(0)
#     line = trend(0)[0]
#     assert np.allclose(line.extremas, [(3, 1), (6, 3.3)])
#     ps.set([(0, 2), (1, 2), (2, 2), (3, 1), (4, 3.4), (5, 2.5), (6, 3.3)])
#     line = trend(0)[0]
#     assert np.allclose(line.extremas, [(3, 1), (4, 3.4)])
