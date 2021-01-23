import math
from .curve import Curve, MIN_STEP
from intervalpy import Interval

PREVIOUS_INTERPOLATION = -1
LINEAR_INTERPOLATION = 0
NEXT_INTERPOLATION = 1

ALL_INTERPOLATIONS = [
    PREVIOUS_INTERPOLATION,
    LINEAR_INTERPOLATION,
    NEXT_INTERPOLATION
]


class Points(Curve):

    class interpolation:

        previous = PREVIOUS_INTERPOLATION
        linear = LINEAR_INTERPOLATION
        next = NEXT_INTERPOLATION

        default = linear
        all = ALL_INTERPOLATIONS

    @property
    def is_uniform(self):
        if self._force_equally_spaced:
            return True
        return self._is_equally_spaced

    def get_domain(self):
        if len(self._points) == 0:
            return Interval.empty()
        return Interval(self._points[0][0], self._points[-1][0], start_open=False, end_open=False)

    def __init__(self, points, interpolation=None, uniform=True):
        """
        `points` are assumed to be strictly ordered in ascending order w.r.t. to `x`.
        """
        super().__init__()
        
        if interpolation is None:
            interpolation = Points.interpolation.default
        if interpolation not in ALL_INTERPOLATIONS:
            raise Exception('Invalid interpolation')
        self.interpolation = interpolation
        self.interval = None
        self._points = []
        self._force_equally_spaced = uniform
        self._is_equally_spaced = None
        self.set(points)

    def append(self, point):
        """
        `points` are assumed to be strictly ordered in ascending order w.r.t. to `x`.
        """
        self.append_list([point])

    def append_list(self, points):
        """
        `points` are assumed to be strictly ordered in ascending order w.r.t. to `x`.
        """
        points_len = len(self._points)
        if points_len == 0:
            return self.set(points)
        new_points_len = len(points)
        if new_points_len == 0:
            return

        if points[0][0] <= self._points[-1][0]:
            raise Exception('Attempting to append points in non-ascending order')

        if self.domain.is_empty:
            domain = Interval.closed(points[0][0], points[-1][0])
        else:
            domain = Interval(self.domain.end, points[-1][0], start_open=True, end_open=False)
        self.begin_update(domain)
        self._is_equally_spaced = self._points_equally_spaced(self._points, points)
        if self._force_equally_spaced and not self._is_equally_spaced:
            raise Exception('Attempting to append points at non-regular intervals: {}{} + {}{}'.format('...' if len(self._points) > 2 else '', self._points[len(self._points) - 2:], points[:2], '...' if len(points) > 2 else ''))
        self._points += points
        self._did_change_points()
        self.end_update(domain)

    def replace(self, point, or_append=False):
        if not self.domain.contains(point[0]):
            if or_append:
                return self.append(point)
            else:
                raise Exception('Attempting to replace point outside of bounds')

        update_domain = Interval.point(point[0])
        self.begin_update(update_domain)

        nearest_i = int(math.ceil(self.x_index(point[0])))
        nearest_p = self._points[nearest_i]
        if point[0] != nearest_p[0]:
            if self._force_equally_spaced:
                raise Exception('Attempting to replace point {} between existing points. The nearest is {}.'.format(point, nearest_p))
            else:
                self._points.insert(nearest_i, point)
                self._is_equally_spaced = False
        else:
            self._points[nearest_i] = point

        self._did_change_points()
        self.end_update(update_domain)    

    def reset(self, domain=None):
        points_len = len(self._points)
        if points_len == 0:
            return
        if domain is None:
            return self.set([])
        domain = Interval.parse(domain)

        if not self.domain.intersects(domain):
            return

        if domain.is_superset_of(self.domain):
            self.set([])
            return

        remove_start_i, remove_end_i = self._domain_indexes(domain)
        if remove_start_i == remove_end_i:
            # Nothing to remove
            return
        head = self._points[:remove_start_i]
        tail = self._points[remove_end_i:]
        if len(head) != 0 and domain.contains(head[-1][0]):
            del head[-1]
        if len(tail) != 0 and domain.contains(tail[0][0]):
            del tail[0]
        head_len = len(head)
        tail_len = len(tail)
        if head_len + tail_len == 0:
            self.set([])
            return
        points = head + tail

        update_start = self._points[0][0]
        update_start_open = False
        if head_len != 0:
            update_start = head[-1][0]
            update_start_open = True

        update_end = self._points[-1][0]
        update_end_open = False
        if tail_len != 0:
            update_end = tail[0][0]
            update_end_open = True

        update_domain = Interval(update_start, update_end, start_open=update_start_open, end_open=update_end_open)

        self.set(points, update_domain=update_domain)

    def set(self, points, update_domain=None):
        """
        `points` are assumed to be strictly ordered in ascending order w.r.t. to `x`.
        """
        if update_domain is None:
            points_len = len(points)
            if points_len == 0:
                update_domain = self.domain
            else:
                update_domain = Interval.union([self.domain, Interval.closed(points[0][0], points[-1][0])])
        self.begin_update(update_domain)
        self._is_equally_spaced = self._points_equally_spaced([], points)
        if self._force_equally_spaced and not self._is_equally_spaced:
            raise Exception('Attempting to set points at non-regular intervals')
        self._points = list(points)
        self._did_change_points()
        self.end_update(update_domain)

    def sample_points(self, domain=None, min_step=None, step=None):
        domain = Interval.parse(domain, default_inf=True)

        if self.domain.is_empty:
            return []

        if self.interval is not None and ((min_step is not None and min_step > self.interval) or (step is not None and step != self.interval)):
            # Irregular sampling
            return super().sample_points(domain=domain, min_step=min_step, step=step)

        if domain is None or domain.is_superset_of(self.domain):
            # Sample all
            return list(self._points)

        # Sample some
        domain = Interval.intersection([self.domain, domain])
        if domain.is_empty:
            return []
        i0, i1 = self._domain_indexes(domain)
        return self._points[i0:i1]

    def _did_change_points(self):
        self.interval = None
        len_points = len(self._points)
        if len_points > 1:
            self.interval = (self._points[-1][0] - self._points[0][0]) / (len_points - 1)

    def _points_equally_spaced(self, old_points, new_points):
        old_points_len = len(old_points)
        new_points_len = len(new_points)
        if new_points_len == 0 or old_points_len + new_points_len < 2:
            return True

        if old_points_len != 0:
            start = old_points[-1][0]
            steps = new_points_len
        else:
            start = new_points[0][0]
            steps = new_points_len - 1

        if self.interval is not None:
            interval = self.interval
        elif old_points_len == 1:
            interval = new_points[0][0] - old_points[-1][0]
        else:
            interval = new_points[1][0] - new_points[0][0]

        expected_last_x = start + interval * steps
        return new_points[-1][0] == expected_last_x

    def y(self, x):
        if not self.domain.contains(x):
            return None
        i_ = self.x_index(x)
        u = i_ % 1.0
        i = int(i_)
        if u == 0:
            return self._points[i][1]
        if self.interpolation == Points.interpolation.linear:
            y1 = self._points[i][1]
            y2 = self._points[i + 1][1]
            if y1 is None or y2 is None:
                return None
            return (1.0 - u) * y1 + u * y2
        elif self.interpolation == Points.interpolation.previous:
            return self._points[i][1]
        elif self.interpolation == Points.interpolation.next:
            return self._points[i + 1][1]
        else:
            raise Exception('Unknown interpolation')

    def y_start(self):
        if self.domain.is_empty:
            return None
        return self._points[0][1]

    def y_end(self):
        if self.domain.is_empty:
            return None
        return self._points[-1][1]

    # TODO: optimise d_y()

    def x_next(self, x, min_step=MIN_STEP, limit=None):
        if self.domain.is_empty:
            return None
        min_step = self.resolve_min_step(min_step)
        if not self.domain.contains(x + min_step, enforce_start=False):
            return None
        if math.isinf(x) and x < 0:
            return self.domain.start
        # i = max(0, int(math.floor(self.x_index(x))) + 1)
        i = max(0, int(math.ceil(self.x_index(x + min_step))))
        return self._points[i][0]

    def x_previous(self, x, min_step=MIN_STEP, limit=None):
        if self.domain.is_empty:
            return None
        min_step = self.resolve_min_step(min_step)
        if not self.domain.contains(x - min_step, enforce_end=False):
            return None
        if math.isinf(x) and x > 0:
            return self.domain.end
        # i = min(len(self._points) - 1, int(math.ceil(self.x_index(x))) - 1)
        i = min(len(self._points) - 1, int(math.floor(self.x_index(x - min_step))))
        return self._points[i][0]

    def x_index(self, x):
        if self.is_uniform:
            if self.interval is None:
                return 0
            return (x - self._points[0][0]) / self.interval
        else:
            i1 = _bisect_points(self._points, x)
            i0 = i1 - 1
            if i0 < 0:
                return i1
            if i1 >= len(self._points):
                return i0
            x0 = self._points[i0][0]
            x1 = self._points[i1][0]
            u = (x - x0) / (x1 - x0)
            return float(i0) + u

    def _domain_indexes(self, domain):
        """
        Turn a domain into start and end indexes (inclusive and exclusive respectively).
        """
        points_len = len(self._points)
        if domain.is_superset_of(self.domain):
            return 0, points_len

        domain = Interval.intersection([domain, self.domain])
        if domain.is_empty:
            return 0, 0

        if domain.is_negative_infinite:
            start_i = 0
        else:
            i = max(0, int(math.floor(self.x_index(domain.start))))
            while i < points_len:
                x = self._points[i][0]
                if x >= domain.end:
                    # i -= 1
                    break
                if domain.contains(x):
                    break
                i += 1
            start_i = i
            
        if domain.is_positive_infinite:
            end_i = points_len
        else:
            i = min(points_len, int(math.ceil(self.x_index(domain.end))))
            while i >= 0:
                x = self._points[i][0]
                if x <= domain.start:
                    # i += 1
                    break
                if domain.contains(x):
                    break
                i -= 1
            end_i = i + 1

        return start_i, end_i

def _bisect_points(a, x, lo=0, hi=None):
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
        if a[mid][0] < x: lo = mid + 1
        else: hi = mid
    return lo
