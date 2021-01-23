from .curve import Curve, MIN_STEP
from intervalpy import Interval
from collections.abc import Sequence


class Aggregate(Curve):

    def get_domain(self):
        domains = list(map(lambda f: f.domain, self.funcs))
        if self.is_union:
            return Interval.union(domains)
        else:
            return Interval.intersection(domains)

    def __init__(self, funcs, *args, tfm=None, default=None, union=False, operator=None, name=None):
        if not isinstance(funcs, Sequence):
            funcs = [funcs] + list(args)
        super().__init__()
        self.funcs = Curve.parse_many(funcs)
        self.tfm = tfm
        self.is_union = union
        self.operator = operator
        self.name = name
        self.default = default
        unique_funcs = list(set(list(self.funcs)))
        self._observer_tokens = list(map(lambda f: f.add_observer(
            begin=self.begin_update, end=self.end_update, prioritize=True), unique_funcs))

    def __del__(self):
        for func, token in zip(self.funcs, self._observer_tokens):
            func.remove_observer(token)

    def __repr__(self):
        try:
            params = ", ".join(list(map(str, self.funcs)))
            return f'{self.name or self.operator or self.util.__name__}({params})'
            # if self.operator is not None:
            #     def child_str(f):
            #         if isinstance(f, Aggregate):
            #             return f'({f})'
            #         else:
            #             return str(f)
            #     return f" {self.operator} ".join(list(map(child_str, self.funcs)))
            # else:
            #     params = ", ".join(list(map(str, self.funcs)))
            #     return f'{self.name or self.util.__name__}({params})'
        except Exception as e:
            return super().__repr__() + f'({e})'

    def y(self, x):
        if not self.domain.contains(x):
            return self.default
        func_vals = list(map(lambda f: f.y(x), self.funcs))
        if self.tfm is None:
            return func_vals
        return self.tfm(x, func_vals)

    def x_previous(self, x, min_step=MIN_STEP, limit=None):
        return max_or_none(map(lambda f: f.x_previous(x, min_step=min_step, limit=limit), self.funcs), x)

    def x_next(self, x, min_step=MIN_STEP, limit=None):
        return min_or_none(map(lambda f: f.x_next(x, min_step=min_step, limit=limit), self.funcs), x)


def min_or_none(iterable, gt):
    min = None
    for item in iterable:
        if item is None:
            continue
        if min is None or item < min:
            if item > gt:
                min = item
    return min


def max_or_none(iterable, lt):
    max = None
    for item in iterable:
        if item is None:
            continue
        if max is None or item > max:
            if item < lt:
                max = item
    return max
