import numpy as np
import math
import copy
# from scipy.optimize import minimize
from collections.abc import Sequence
from .scan import Scan
from .curve import MIN_STEP
from intervalpy import Interval
from .const import GOLD, GOLD_2

TOL_REL_DEFAULT = 0.01
SEARCH_WIDTH_REL_DEFAULT = 10.0
SEARCH_WIDTH_INT_REL_DEFAULT = 2.0
EPSILON_ZERO = 1e-14

MAX_COUNT = 1000

class Trend(Scan):
    """
    Only forward direction is supported.
    """

    def get_domain(self):
        return super().get_domain().extended_to_positive_infinity()

    def __init__(self, func, min_width, min_points=3, min_point_distance=0, search_length_rel=SEARCH_WIDTH_REL_DEFAULT, search_length_int_rel=SEARCH_WIDTH_INT_REL_DEFAULT, x_tol_rel=None, x_tol_abs=None, y_tol_rel=None, y_tol_abs=None, min_step=MIN_STEP):
        self.min_width = min_width
        self.min_points = min_points
        self.min_point_distance = min_point_distance
        self.search_length_rel = search_length_rel
        self.search_length_int_rel = search_length_int_rel

        if x_tol_rel is None and x_tol_abs is None:
            x_tol_rel = TOL_REL_DEFAULT
        if y_tol_rel is None and y_tol_abs is None:
            y_tol_rel = TOL_REL_DEFAULT

        self.x_tol_rel = x_tol_rel
        self.x_tol_abs = x_tol_abs
        self.y_tol_rel = y_tol_rel
        self.y_tol_abs = y_tol_abs

        self.points = []
        self.nested_upper_lines = [[]]
        self.nested_lower_lines = [[]]
        
        super().__init__(func, self._trend_scan, min_step=min_step)

    @property
    def lines(self):
        return self._scanned_lower(None) + self._scanned_upper(None)

    def upper(self, x):
        if x is not None:
            self.scan(x)
        return self._scanned_upper(x)

    def lower(self, x):
        if x is not None:
            self.scan(x)
        return self._scanned_lower(x)

    def scanned_y(self, x):
        return self._scanned_lower(x) + self._scanned_upper(x)

    def continue_scan(self, x):
        if super().continue_scan(x):
            return True
        if not self.domain.contains(self.current):
            return False

        is_empty = True

        # for line in self.lines:
        #     is_empty = False
        #     if line.search_interval.contains(x, enforce_end=False):
        #         return True

        for lines in self.nested_upper_lines:
            for line in lines:
                is_empty = False
                if line.search_interval.contains(x, enforce_end=False):
                    return True

        for lines in self.nested_lower_lines:
            for line in lines:
                is_empty = False
                if line.search_interval.contains(x, enforce_end=False):
                    return True

        return is_empty

    def begin_update(self, domain):
        super().begin_update(domain)

        # remove stale points
        for i in reversed(range(len(self.points))):
            p = self.points[i]
            if domain.contains(p[0]):
                del self.points[i]
            elif p[0] < domain.start:
                break

        def update_nested_line_array(nested_lines):
            for i in reversed(range(len(nested_lines))):
                lines = nested_lines[i]
                update_line_array(lines)
                if i != 0 and len(lines) == 0:
                    del nested_lines[i]

        def update_line_array(lines):
            for i in reversed(range(len(lines))):
                line = lines[i]
                line.begin_update(domain, self.points)
                if line.is_empty:
                    del lines[i]

        # update_line_array(self.lines)
        update_nested_line_array(self.nested_upper_lines)
        update_nested_line_array(self.nested_lower_lines)

    def _scanned_upper(self, x):
        filtered_lines = []
        for lines in self.nested_upper_lines:
            for line in lines:
                if self._line_filter(line, x):
                    filtered_lines.append(line)
        return filtered_lines

    def _scanned_lower(self, x):
        filtered_lines = []
        for lines in self.nested_lower_lines:
            for line in lines:
                if self._line_filter(line, x):
                    filtered_lines.append(line)
        return filtered_lines

    def _line_filter(self, line, x):
        if not line.is_valid:
            return False
        if x is not None and not line.search_interval.contains(x):
            return False
        if self.min_width is not None and line.width < self.min_width:
            return False
        return True

    def _trend_scan(self, x, y):
        if y is None:
            return
        p = (x, y)
        self.points.append(p)
        
    #     self._did_append_nested_point(p, self.nested_upper_lines, is_upper_trend=True)
    #     self._did_append_nested_point(p, self.nested_lower_lines, is_upper_trend=False)

    # def _did_append_nested_point(self, nested_p, nested_lines, is_upper_trend=True):
        i = 0
        points = [p]
        while i < len(self.nested_upper_lines):
            all_trend_points = []
            for p in points:
                new_trend_points = self._append_point_and_validate(p, self.nested_upper_lines[i], self.nested_upper_lines, is_upper_trend=True)
                _insort_points_left(all_trend_points, new_trend_points)

                new_trend_points = self._append_point_and_validate(p, self.nested_lower_lines[i], self.nested_lower_lines, is_upper_trend=False)
                _insort_points_left(all_trend_points, new_trend_points)
            if len(all_trend_points) == 0:
                break
            # print('found {} trend line(s) at {} (depth {}/{})'.format('upper' if is_upper_trend else 'lower', nested_p, i, len(nested_lines)))
            # print(list(map(lambda l: l.trend_points, nested_lines[i])))
            i += 1
            points = all_trend_points
            if len(self.nested_upper_lines) == i:
                self.nested_upper_lines.append([])
                self.nested_lower_lines.append([])

    def _append_point_and_validate(self, p, lines, nested_lines, is_upper_trend=True):
        remove_indexes = []
        new_trend_points = []

        for i, line in enumerate(lines):
            was_valid = line.is_valid
            was_ready = line.is_ready

            if line.did_append_point(p, self.points):
                if line.is_valid:
                    if not was_valid:
                        if self._has_coincident_nested_line(line, nested_lines):
                            # trend already added
                            remove_indexes.append(i)
                            continue

                        # We can't add all trend points because it would form a trend line
                        # on a deeper level and would cause an infinite loop.
                        _insort_point_left(new_trend_points, line.trend_points[0], no_repeat=True)
                        _insort_point_left(new_trend_points, line.trend_points[-1], no_repeat=True)

                elif line.is_ready and not was_ready and self._has_coincident_line(line, lines):
                    # already tracking this trend
                    remove_indexes.append(i)
                    continue

        for i in reversed(remove_indexes):
            del lines[i]

        self._try_fork_line(lines, p, is_upper_trend=is_upper_trend)

        return new_trend_points

    def _try_fork_line(self, lines, p, is_upper_trend=True):
        if len(lines) != 0:
            last_line = lines[-1]
            if not last_line.is_ready or p[0] - last_line.trend_points[0][0] < last_line.min_width:
                return None

        line = self._create_line(is_upper_trend=is_upper_trend)
        line.did_append_point(p, self.points)
        lines.append(line)
        return line

    def _create_line(self, is_upper_trend=True):
        return TrendLine(self.min_width,
            is_upper_trend=is_upper_trend,
            min_points=self.min_points, 
            search_length_rel=self.search_length_rel, 
            search_length_int_rel=self.search_length_int_rel, 
            x_tol_rel=self.x_tol_rel, 
            x_tol_abs=self.x_tol_abs, 
            y_tol_rel=self.y_tol_rel, 
            y_tol_abs=self.y_tol_abs)

    def _has_coincident_nested_line(self, line, nested_lines):
        for lines in nested_lines:
            if self._has_coincident_line(line, lines):
                return True
        return False

    def _has_coincident_line(self, line, lines):
        for other_line in lines:
            if other_line == line or not other_line.is_ready or not line.search_interval.intersects(other_line.search_interval):
                continue
            if other_line.is_line_coincident(line):
                return True
        return False

class TrendLine(Sequence):

    PREDICTION_PHASE_NONE = 0
    PREDICTION_PHASE_INTERSECTED = 1
    PREDICTION_PHASE_RETESTED = 2
    PREDICTION_PHASE_CONFIRMED = 3
    PREDICTION_PHASE_FULFILLED = 4

    @property
    def is_lower_trend(self):
        return not self.is_upper_trend

    @property
    def is_valid(self):
        """Return `True` if all trend line requirements are satisfied."""
        trend_points_count = len(self.trend_points)

        if not self.is_ready or self.width < self.min_width or trend_points_count < self.min_points:
            return False

        # Check distance between trend points
        distance_valid_count = 1
        for i in range(1, trend_points_count):
            if self.trend_points[i][0] - self.trend_points[i - 1][0] >= self.min_point_distance:
                distance_valid_count += 1
                if distance_valid_count >= self.min_points:
                    break

        if distance_valid_count < self.min_points:
            return False

        return True

    @property
    def is_ready(self):
        """Return `True` if there is enough trend points to form a line."""
        return self._line is not None 

    @property
    def is_empty(self):
        """Return `True` where there are no trend points."""
        return len(self.trend_points) == 0

    @property
    def width(self):
        return self.trend_points[-1][0] - self.trend_points[0][0] if len(self.trend_points) >= 2 else 0

    def line_extended(self, width_mult=None, width_max=None, intersection_index=None):
        if not self.is_ready:
            return None
        x0, y0 = self._line[0]
        x1 = self._line[1][0]
        intersection_count = len(self.intersections)
        if intersection_index is not None and intersection_count != 0:
            if intersection_index < 0:
                intersection_index = max(0, len(self.intersections) + intersection_index)
            else:
                intersection_index = min(intersection_index, len(self.intersections) - 1)
            intersection = self.intersections[intersection_index]
            if intersection[0] > x1:
                x1 = intersection[0]
        if width_mult is not None:
            x1 = x0 + (x1 - x0) * width_mult
        if width_max is not None and x1 - x0 > width_max:
            x1 = x0 + width_max
        if intersection_index is not None and intersection_index + 1 < intersection_count:
            next_intersection = self.intersections[intersection_index + 1]
            if next_intersection[0] < x1:
                x1 = next_intersection[0]            
        y1 = self.y(x1)
        return [(x0, y0), (x1, y1)]

    def __init__(self, min_width, is_upper_trend=True, min_points=None, min_point_distance=0, search_length_rel=None, search_length_int_rel=None, x_tol_rel=None, x_tol_abs=None, y_tol_rel=None, y_tol_abs=None):
        self.min_width = min_width
        self.is_upper_trend = is_upper_trend
        self.min_points = min_points
        self.min_point_distance = min_point_distance
        self.search_length_rel = search_length_rel
        self.search_length_int_rel = search_length_int_rel
        self.x_tol_rel = x_tol_rel
        self.x_tol_abs = x_tol_abs
        self.y_tol_rel = y_tol_rel
        self.y_tol_abs = y_tol_abs

        """A list of points through which the trend line is formed."""
        self.trend_points = []
        """An unfiltered list of points from which trend points are derived."""
        self._boundary_points = []
        """A list of points which touch the trend line without the underlying trend crossing the trend."""
        self.tangent_points = []

        self._line = None
        self.search_interval = Interval.empty()
        self.reset_points_of_interest()
        self.reset_prediction()

    def __len__(self):
        return 2 if self.is_ready else 0

    def __getitem__(self, i):
        return self._line[i]

    def __iter__(self):
        if not self.is_ready:
            return
        yield self._line[0]
        yield self._line[1]

    def __copy__(self):
        line = TrendLine(self.min_width,
            is_upper_trend=self.is_upper_trend,
            min_points=self.min_points,
            min_point_distance=self.min_point_distance,
            search_length_rel=self.search_length_rel,
            search_length_int_rel=self.search_length_int_rel,
            x_tol_rel=self.x_tol_rel, 
            x_tol_abs=self.x_tol_abs, 
            y_tol_rel=self.y_tol_rel, 
            y_tol_abs=self.y_tol_abs)
        line.trend_points = list(self.trend_points)
        line._boundary_points = list(self._boundary_points)
        line._line = tuple(self._line)
        line.search_interval = self.search_interval.copy()
        line.intersections = list(self.intersections)
        line.tangent_points = list(self.tangent_points)
        return line

    def copy(self):
        return copy.copy(self)

    def y(self, x):
        """Return the y value at which the `line` crosses the vertical line at `x`."""
        return _line_y(self._line, x)

    def x(self, y):
        """Return the x value at which the `line` crosses the horizontal line at `y`."""
        return _line_x(self._line, y)

    def is_point_on_trend(self, p):
        if self._line is None or not self.search_interval.contains(p[0]):
            return False
        return p[1] >= self._y_min(p[0]) and p[1] <= self._y_max(p[0])
        # return self._is_value_within_tolerance(p[1], self.y(p[0]))
        # return self._is_line_fit_within_tolerance(self.trend_points + [p])

    def is_line_coincident(self, line):
        for p_line in line._line:
            if not self.is_point_on_trend(p_line):
                return False
        return True
        # return self._is_line_fit_within_tolerance(self.trend_points + line.trend_points)

    def set_trend_with_boundary_points(self):
        extremas = list(self._boundary_points)
        coincident_points = []

        # remove all linear and convex (concave) maximas (minimas)
        did_remove = True
        while did_remove:
            did_remove = False
            for i in reversed(range(0, len(extremas) - 2)):
                points = extremas[i:i + 3]
                is_coincident = _is_coincident_points(points, y_tol_rel=self.y_tol_rel, y_tol_abs=self.y_tol_abs)
                is_convex = _is_strictly_convex_points(points, y_tol_rel=self.y_tol_rel, y_tol_abs=self.y_tol_abs)
                if is_coincident or is_convex == self.is_upper_trend:
                    p = extremas[i + 1]
                    if is_coincident and (len(coincident_points) == 0 or coincident_points[-1][0] != p[0]):
                        coincident_points.append(p)
                    if not is_coincident:
                        del self._boundary_points[i + 1]
                    del extremas[i + 1]
                    did_remove = True

        # remove all points which are too close together
        for i in reversed(range(0, len(extremas) - 2)):
            p0, p1, p2 = extremas[i:i + 3]
            if p1[0] - p0[0] < self.min_point_distance or p2[0] - p1[0] < self.min_point_distance:
                del extremas[i + 1]

        final_line = extremas

        extremas_len = len(extremas)
        if extremas_len > 2:
            # Reduce to 2 extremas
            # keep extremas which minimise square error
            lines = []
            for i in range(0, extremas_len - 1):
                lines.append(extremas[i:i + 2])

            def line_fitness(line):
                error_sum = 0
                for p in self._boundary_points:
                    error_sum += math.pow(p[1] - _line_y(line, p[0]), 2.0)
                return error_sum

            lines = sorted(lines, key=line_fitness)
            final_line = lines[0]

        def add_coincident_points(line, coincident_points):
            line_len = len(line)
            if line_len < 2:
                return line
            elif line_len > 2:
                raise Exception("Expected line")
            resulting_points = []
            for p in coincident_points:
                if _is_point_on_line(line, p, y_tol_rel=self.y_tol_rel, y_tol_abs=self.y_tol_abs):
                    resulting_points.append(p)
            resulting_points.insert(0, line[0])
            resulting_points.append(line[1])
            return resulting_points

        final_points = add_coincident_points(final_line, coincident_points)
        self.trend_points = final_points

    def did_append_point(self, p, underlying_points):
        if self.is_ready and not self.search_interval.contains(p[0]):
            return False

        if not self.is_valid:
            _insort_point_left(self._boundary_points, p, no_repeat=True)
            self.update_trend(underlying_points)
            return True
        elif self.is_point_on_trend(p):
            # Point is on the existing line.
            _insort_point_left(self._boundary_points, p, no_repeat=True)
            _insort_point_left(self.trend_points, p, no_repeat=True)
            self.update_trend(underlying_points)
            return True
        else:
            did_change = self.update_points_of_interest(underlying_points)
            self.update_prediction(underlying_points)
            return did_change
        
        return False

    def begin_update(self, domain, underlying_points):
        if not self.search_interval.intersects(domain):
            return

        # remove stale points
        did_remove = False

        def remove_stale(points):
            did_remove = False
            for i in reversed(range(len(points))):
                p = points[i]
                if domain.contains(p[0]):
                    del points[i]
                    did_remove = True
                elif p[0] < domain.start:
                    break
            return did_remove

        if remove_stale(self.trend_points):
            did_remove = True
        if remove_stale(self._boundary_points):
            did_remove = True
        if remove_stale(self.intersections):
            did_remove = True
        if remove_stale(self.tangent_points):
            did_remove = True
        if remove_stale(self.extremas):
            did_remove = True

        if did_remove:
            self.update_trend(underlying_points)

    def update_trend(self, underlying_points):
        if not self.is_valid:
            self.set_trend_with_boundary_points()

        self._line = _line_fit(self.trend_points)
        self._update_trend_tolerance_lines()
        self.reset_points_of_interest()
        self.update_points_of_interest(underlying_points)
        self.update_interval()
        self.reset_prediction()
        self.update_prediction(underlying_points)

    def update_interval(self):
        len_trend_points = len(self.trend_points)
        if self._line is None:
            if len_trend_points == 1:
                self.search_interval = Interval.point(self.trend_points[0][0])
            else:
                self.search_interval = Interval.empty()
            return

        p0, p1 = self._line
        if p0[0] == p1[0]:
            # vertical line
            self.search_interval = Interval.point(p0[0])
            return

        if self.search_length_rel <= 0:
            self.search_interval = Interval.closed(p0[0], p1[0])
            return

        x_min = p0[0]
        x_max = p1[0]

        intersection = self.intersections[0] if len(self.intersections) != 0 else None
        if intersection is not None and intersection[0] <= x_min:
            intersection = None

        if intersection is None or len_trend_points >= self.min_points:
            # search ahead
            x_length = (x_max - x_min) * self.search_length_rel
        else:
            # not enought points to go through intersection
            x_length = intersection[0] - x_min

        # if intersection is None:
        #     # search ahead
        #     x_length = (x_max - x_min) * self.search_length_rel
        # elif len_trend_points >= self.min_points:
        #     # search ahead of intersection
        #     x_length = (intersection[0] - x_min) * self.search_length_int_rel
        # else:
        #     # not enought points to go through intersection
        #     x_length = intersection[0] - x_min

        x_max = x_min + x_length

        self.search_interval = Interval.closed_open(x_min, x_max)

    def reset_points_of_interest(self):
        self.intersections = []
        self.tangent_points = []
        self.extremas = []

    def update_points_of_interest(self, underlying_points):
        if not self.is_ready:
            return False

        i_end = len(underlying_points)
        if i_end == 0:
            return False

        def process_points_on_trend(points_on_trend, insert_index):
            if len(points_on_trend) == 0:
                return
            closest_point = None
            closest_dist = 0
            for p in points_on_trend:
                dist = abs(self.y(p[0]) - p[1])
                if closest_point is None or dist < closest_dist:
                    closest_dist = dist
                    closest_point = p
            self.tangent_points.insert(insert_index, closest_point)

        # find intersections, tangent points and extremas
        phase = 0
        phase_point = None
        previous_phase = phase
        intersection_found = False
        intersection_insert_index = len(self.intersections)
        tangent_insert_index = len(self.tangent_points)
        points_on_trend = []
        new_extremas = []
        extrema = None
        extrema_dist = 0

        # search up to the last intersection or tangent point
        update_interval = self.search_interval
        if len(self.intersections) != 0:
            update_interval = Interval.intersection([update_interval, Interval.gte(self.intersections[-1][0])])
        if len(self.tangent_points) != 0:
            update_interval = Interval.intersection([update_interval, Interval.gt(self.tangent_points[-1][0])])

        for i in reversed(range(len(underlying_points))):
            p = underlying_points[i]
            if not update_interval.contains(p[0]):
                break
            
            if self.is_point_on_trend(p):
                points_on_trend.insert(0, p)
                if extrema is not None:
                    new_extremas.insert(0, extrema)
                    extrema = None
                continue
            elif len(points_on_trend) != 0:
                process_points_on_trend(points_on_trend, tangent_insert_index)
                points_on_trend = []

            phase = p[1] - self.y(p[0])
            at_intersection = previous_phase != 0 and phase * previous_phase < 0

            if at_intersection:
                # found intersection
                intersection = _line_intersection(self._line, (phase_point, p))
                if intersection is None or intersection[0] < self._line[0][0]:
                    intersection = _average_point_of_2(phase_point, p)
                self.intersections.insert(intersection_insert_index, intersection)
                intersection_found = True

                if extrema is not None:
                    new_extremas.insert(0, extrema)
                    extrema = None

            if phase > 0:
                dist = p[1]
            else:
                dist = -p[1]
            if extrema is None or dist > extrema_dist:
                extrema = p
                extrema_dist = dist

            previous_phase = phase
            phase_point = p

        if len(points_on_trend) != 0:
            process_points_on_trend(points_on_trend, tangent_insert_index)

        if extrema is not None:
            new_extremas.insert(0, extrema)
        if len(new_extremas) != 0:
            # merge extremas with existing ones
            if len(self.extremas) == 0:
                self.extremas += new_extremas
            else:
                if self.extremas[-1][0] >= update_interval.start:
                    # old extrema may be outdated
                    del self.extremas[-1]
                self.extremas += new_extremas

        if intersection_found:
            self.update_interval()

        return intersection_found

    def reset_prediction(self):
        self.prediction_phase = TrendLine.PREDICTION_PHASE_NONE
        self.prediction_origin = None
        self.prediction_intersection = None
        self.prediction_extrema = None
        self.prediction_retest_point = None
        self.prediction_retest_x_max = None
        self.prediction_trend_line = None
        self.prediction_confirmation_line = None
        self.prediction_y = None
        self.prediction_y_min = None
        self.prediction_y_max = None
        self.prediction_x_min = None
        self.prediction_x_max = None
        self.prediction_line = None
        self.prediction_failed = False
        self.prediction_succeeded = False
        self.prediction_success_point = None
        self.prediction_valid = False
        self._prediction_last_seen_extrema_point = None
        self._prediction_x_processed = None
        self._prediction_tangent_before_intersection_count = 0

    def update_prediction(self, underlying_points):
        if not self.is_valid:
            return

        self.prediction_origin = self._line[0]

        TYPE_EXTREMA = 1
        TYPE_TANGENT = 2
        TYPE_INTERSECTION = 3

        if self.is_upper_trend:
            extrema_filter = filter(lambda p: p[1] > self.y(p[0]), self.extremas)
        else:
            extrema_filter = filter(lambda p: p[1] < self.y(p[0]), self.extremas)
        extremas = list(map(lambda p: (p[0], p[1], TYPE_EXTREMA), extrema_filter))
        tangents = list(map(lambda p: (p[0], p[1], TYPE_TANGENT), self.tangent_points))
        intersections = list(map(lambda p: (p[0], p[1], TYPE_INTERSECTION), self.intersections))
        points = sorted(extremas + tangents + intersections, key=lambda p: p[0])

        def update_prediction_target():
            nonlocal points

            if self.prediction_intersection is None:
                raise Exception("Should have seen an intersection: {}".format(points))
            if self._prediction_last_seen_extrema_point is None:
                return False

            self.prediction_extrema = self._prediction_last_seen_extrema_point
            self.prediction_confirmation_line = [self.prediction_origin, self.prediction_extrema]
            self.prediction_y = self.prediction_intersection[1] + (self.prediction_extrema[1] - self.prediction_intersection[1]) * GOLD_2
            self.prediction_y_min = self._value_tolerance_min(self.prediction_y)
            self.prediction_y_max = self._value_tolerance_max(self.prediction_y)
            self.prediction_x_min = self.prediction_extrema[0]
            self.prediction_x_max = self.prediction_x_min + (self.prediction_extrema[0] - self.prediction_origin[0]) * GOLD
            self.prediction_line = [(self.prediction_extrema[0], self.prediction_y), (self.prediction_x_max, self.prediction_y)]
            self.prediction_trend_line = [self.prediction_origin, (self.prediction_x_max, self.y(self.prediction_x_max))]

            self.prediction_valid = self.prediction_y > 0

            return True

        if len(points) == 0:
            return

        for p in points:
            if self._prediction_x_processed is not None and p[0] < self._prediction_x_processed:
                continue
            point_type = p[2]
            clean_point = (p[0], p[1])
            if self.prediction_succeeded or self.prediction_failed:
                break
            elif self.prediction_phase == TrendLine.PREDICTION_PHASE_NONE:
                # Look for intersection
                if point_type == TYPE_TANGENT:
                    self._prediction_tangent_before_intersection_count += 1
                if point_type == TYPE_INTERSECTION:
                    if self._prediction_tangent_before_intersection_count < self.min_points:
                        self.prediction_failed = True
                        self.prediction_valid = False
                        break
                    self.prediction_phase = TrendLine.PREDICTION_PHASE_INTERSECTED
                    self.prediction_intersection = clean_point
                    self.prediction_retest_x_max = self.prediction_intersection[0] + (self.prediction_intersection[0] - self.prediction_origin[0]) / GOLD
                    self.prediction_trend_line = [self.prediction_origin, (self.prediction_retest_x_max, self.y(self.prediction_retest_x_max))]
                continue

            # Look for extrema and retest points
            if point_type == TYPE_EXTREMA:
                self._prediction_last_seen_extrema_point = clean_point

                if self.prediction_phase == TrendLine.PREDICTION_PHASE_INTERSECTED:
                    # Update prediction targets
                    if not update_prediction_target():
                        self.prediction_failed = True
                        break

                if self.prediction_phase == TrendLine.PREDICTION_PHASE_RETESTED:
                    # Check for confirmation
                    confirmation_y = _line_y(self.prediction_confirmation_line, p[0])
                    confirmation_y_min = self._value_tolerance_min(confirmation_y)
                    confirmation_y_max = self._value_tolerance_max(confirmation_y)
                    if (self.is_upper_trend and p[1] >= confirmation_y_max) or (self.is_lower_trend and p[1] <= confirmation_y_min):
                        self.prediction_phase = TrendLine.PREDICTION_PHASE_CONFIRMED
                
                if self.prediction_phase == TrendLine.PREDICTION_PHASE_CONFIRMED:
                    # Check for prediction fulfilment
                    if (self.is_upper_trend and p[1] >= self.prediction_y_min) or (self.is_lower_trend and p[1] <= self.prediction_y_max):
                        self.prediction_phase = TrendLine.PREDICTION_PHASE_FULFILLED
                        self.prediction_succeeded = True
                        self.prediction_success_point = clean_point
                        break
                    elif p[0] >= self.prediction_x_max:
                        self.prediction_failed = True
                        break
            elif point_type == TYPE_TANGENT:
                if p[0] > self.prediction_retest_x_max:
                    # Retest too far from intersection
                    self.prediction_failed = True
                    break
                # Retested, prediction is ready.
                # Note: There may be more than one retest, take the last one
                if not update_prediction_target():
                    self.prediction_failed = True
                    break
                self.prediction_phase = TrendLine.PREDICTION_PHASE_RETESTED
                self.prediction_retest_point = clean_point
            elif point_type == TYPE_INTERSECTION:
                # Intersected the trend line again, i.e. retest failed
                self.prediction_failed = True
                break

        if not self.prediction_succeeded and not self.prediction_failed:
            self._prediction_x_processed = points[-1][0]

            # Check prediction timeouts
            last_underlying_point = underlying_points[-1]
            if self.prediction_phase >= TrendLine.PREDICTION_PHASE_RETESTED:
                if last_underlying_point[0] >= self.prediction_x_max:
                    self.prediction_failed = True
            if self.prediction_phase == TrendLine.PREDICTION_PHASE_INTERSECTED:
                if last_underlying_point[0] >= self.prediction_retest_x_max:
                    self.prediction_failed = True

    def _is_line_fit_within_tolerance(self, points):
        if len(points) <= 2:
            return True

        fit_f = _line_fit_f(points)
        for p in points:
            y_line = fit_f(p[0])
            if not self._is_value_within_tolerance(p[1], y_line):
                return False
        return True

    def _is_value_within_tolerance(self, y, ref_y):
        if y is None or ref_y is None:
            return False
        return y < self._value_tolerance_min(ref_y) or y > self._value_tolerance_max(ref_y)

    def _value_tolerance_min(self, y):
        y_min = None
        if self.y_tol_abs is not None:
            y_min = y - self.y_tol_abs
        if self.y_tol_rel is not None and abs(y) > EPSILON_ZERO:
            y_min_rel = y * (1 - self.y_tol_rel)
            if y_min is None:
                y_min = y_min_rel
            else:
                y_min = max(y_min, y_min_rel)
        if y_min is None:
            y_min = y
        return y_min

    def _value_tolerance_max(self, y):
        y_max = None
        if self.y_tol_abs is not None:
            y_max = y + self.y_tol_abs
        if self.y_tol_rel is not None and abs(y) > EPSILON_ZERO:
            y_max_rel = y * (1 + self.y_tol_rel)
            if y_max is None:
                y_max = y_max_rel
            else:
                y_max = min(y_max, y_max_rel)
        if y_max is None:
            y_max = y
        return y_max
    
    def _y_min(self, x):
        return _line_y(self._tolerance_line_lower, x)

    def _y_max(self, x):
        return _line_y(self._tolerance_line_upper, x)

    def _update_trend_tolerance_lines(self):
        self._tolerance_line_upper = self._calculate_trend_tolerance_line(is_upper=True)
        self._tolerance_line_lower = self._calculate_trend_tolerance_line(is_upper=False)

    def _calculate_trend_tolerance_line(self, is_upper=True):
        line = self._line

        trend_points_count = len(self.trend_points)
        if trend_points_count < 2:
            return None
        # elif trend_points_count == 2:
        else:
            x0 = line[0][0]
            x1 = line[1][0]
            if is_upper:
                y0 = self._value_tolerance_max(line[0][1])
                y1 = self._value_tolerance_max(line[1][1])
            else:
                y0 = self._value_tolerance_min(line[0][1])
                y1 = self._value_tolerance_min(line[1][1])
            return [(x0, y0), (x1, y1)]

        # slope = (line[1][1] - line[0][1]) / (line[1][0] - line[0][0])
        # const = _line_y(line, 0)
        # params = [const, slope]

        # def error_func(params_attempt):
        #     const, slope = params_attempt
        #     error_sum = 0

        #     for p in self.trend_points:
        #         y_line = const + slope * p[0]
        #         if is_upper:
        #             y_max = self._value_tolerance_max(p[1])
        #             err = (y_line - y_max) ** 2
        #             if y_line > y_max:
        #                 err *= 1e5
        #         else:
        #             y_min = self._value_tolerance_min(p[1])
        #             err = (y_line - y_min) ** 2
        #             if y_line < y_min:
        #                 err *= 1e5
        #         error_sum += err
        #     return error_sum
            

        # # docs: https://docs.scipy.org/doc/scipy-0.18.1/reference/generated/scipy.optimize.minimize.html#scipy.optimize.minimize
        # x0 = list(params)
        # method = 'Nelder-Mead'
        # tolerance = 1e-6
        # result = minimize(error_func, x0, method=method, tol=tolerance)
        # params = list(result.x)
        # const, slope = params
        # x0 = line[0][0]
        # y0 = const + slope * x0
        # x1 = line[1][0]
        # y1 = const + slope * x1
        # return [(x0, y0), (x1, y1)]

def _line_fit_f(points):
    points_t = np.transpose(points)
    x = points_t[0]
    y = points_t[1]
    fit = np.polyfit(x, y, 1)
    fit_f = np.poly1d(fit)
    return fit_f

def _line_fit(points):
    if len(points) < 2:
        return None
    if len(points) == 2:
        return points

    # describe line with two points
    fit_f = _line_fit_f(points)
    x0 = points[0][0]
    x1 = points[-1][0]
    p1 = [x0, fit_f(x0)]
    p2 = [x1, fit_f(x1)]

    return [p1, p2]

def _is_line_fit_within_tolerance(points, y_tol_rel=None, y_tol_abs=None):
    if len(points) <= 2:
        return True

    fit_f = _line_fit_f(points)
    for p in points:
        y_line = fit_f(p[0])
        if not _is_value_within_tolerance(p[1], y_line, y_tol_rel=y_tol_rel, y_tol_abs=y_tol_abs):
            return False
    return True

def _line_intersection(line1, line2):
    xdiff = (line1[0][0] - line1[1][0], line2[0][0] - line2[1][0])
    ydiff = (line1[0][1] - line1[1][1], line2[0][1] - line2[1][1])

    def det(a, b):
        return a[0] * b[1] - a[1] * b[0]

    div = det(xdiff, ydiff)
    if div == 0:
       return None

    d = (det(*line1), det(*line2))
    x = det(d, xdiff) / div
    y = det(d, ydiff) / div
    return [x, y]

def _is_strictly_convex_points(points, y_tol_rel=None, y_tol_abs=None):
    """
    A function is strictly convex if the line segment between any two points on the graph of the function lies above the graph.
    """
    if len(points) != 3:
        raise Exception("Expected 3 points")
    x = points[1][0]
    y = points[1][1]
    y0 = _line_y((points[0], points[2]), x)
    
    if y0 is None:
        return False
    if y_tol_abs is not None and y0 - y < y_tol_abs:
        return False
    if y_tol_rel is not None and abs(y0) > EPSILON_ZERO and abs(y) > EPSILON_ZERO and y0 / y - 1 < y_tol_rel:
        return False
    return True

def _is_coincident_points(points, y_tol_rel=None, y_tol_abs=None):
    if len(points) != 3:
        raise Exception("Expected 3 points")
    return _is_point_on_line((points[0], points[2]), points[1], y_tol_rel=y_tol_rel, y_tol_abs=y_tol_abs)

def _is_point_on_line(line, p, y_tol_rel=None, y_tol_abs=None):
    x = p[0]
    y = p[1]
    y0 = _line_y(line, x)
    return _is_value_within_tolerance(y, y0, y_tol_rel=y_tol_rel, y_tol_abs=y_tol_abs)

def _is_value_within_tolerance(y, y0, y_tol_rel=None, y_tol_abs=None):
    if y is None or y0 is None:
        return False
    if y_tol_abs is not None and abs(y - y0) > y_tol_abs:
        return False
    if y_tol_rel is not None and abs(y0) > EPSILON_ZERO and abs(y) > EPSILON_ZERO and abs(y / y0 - 1) > y_tol_rel:
        return False
    return True

def _line_y(line, x):
    """Return the y value at which the `line` crosses the vertical line at `x`."""
    p1 = line[0]
    p2 = line[1]
    if p2[0] == p1[0]:
        if p1[0] == x:
            return p1[1]
        return None
    m = (p2[1] - p1[1]) / (p2[0] - p1[0])
    y = p1[1] + m * (x - p1[0])
    return y

def _line_x(line, y):
    """Return the x value at which the `line` crosses the horizontal line at `y`."""
    p1 = line[0]
    p2 = line[1]
    if p2[0] == p1[0]:
        return p1[0]
    m = (p2[1] - p1[1]) / (p2[0] - p1[0])
    if m == 0:
        if p1[1] == y:
            return p1[0]
        return None
    x = p1[0] + (y - p1[1]) / m
    return x

def _insort_points_left(sorted_points, insert_points, lo=0, hi=None, no_repeat=False):
    for p in insert_points:
        _insort_point_left(sorted_points, p, lo=lo, hi=hi, no_repeat=no_repeat) 

def _insort_point_left(a, p, lo=0, hi=None, no_repeat=False):
    """
    Insert point `p` in list `a`, and keep it sorted assuming `a` is sorted.
    If `p` is already in `a`, insert it to the left of the leftmost `p` if `no_repeat` is `False`.
    Optional args `lo` (default `0`) and `hi` (default `len(a)`) bound the
    slice of `a` to be searched.

    Source: https://github.com/python/cpython/blob/master/Lib/bisect.py
    """

    if lo < 0:
        raise ValueError('lo must be non-negative')
    a_len = len(a)
    if hi is None:
        hi = a_len
    while lo < hi:
        mid = (lo + hi) // 2
        if a[mid][0] < p[0]: lo = mid + 1
        else: hi = mid
    if no_repeat and lo < a_len and p[0] == a[lo][0]:
        # repeated point
        return
    a.insert(lo, p)

def _average_point_of_2(p1, p2):
    return ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)