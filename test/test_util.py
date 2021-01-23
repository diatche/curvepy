import pytest
import arrow
import math
import numpy as np
from numbers import Number
from typing import Mapping, Iterable, Any, Sequence, List


def point_gen(values, t_start=0.0, t_step=1.0):
    points = []
    for i in range(len(values)):
        t = t_start + float(i) * t_step
        points.append([t, values[i]])
    return points


def flatten(items) -> list:
    return list(_flatten(items))


def _flatten(items):
    if items is None or isinstance(items, (str, bytes, Mapping)) or not isinstance(items, Iterable):
        yield items
        return
    for x in items:
        if isinstance(x, Iterable) and not isinstance(x, (str, bytes)):
            for sub_x in _flatten(x):
                yield sub_x
        else:
            yield x


def timestamp(x: Any) -> float:
    if x is None:
        raise ValueError(f'Cannot parse timestamp: {x}')
    if isinstance(x, Number):
        if math.isinf(x) or math.isnan(x):
            raise ValueError(f'Cannot parse timestamp: {x}')
        return x
    return arrow.get(x).float_timestamp


def value_for_key(d, key, map=None, skip=[None], default=None):
    if not bool(d):
        return default
    if not isinstance(key, (str, bytes)) and isinstance(key, Sequence):
        # Key path
        return value_for_key_path(d, key, map=map, skip=skip, default=default)
    skip = flatten(skip)
    val = default
    if key in d:
        x = d[key]
        if x not in skip:
            if callable(map):
                try:
                    x = map(x)
                except Exception:
                    x = default
            elif isinstance(map, Mapping):
                x = map[x]
            val = x
    return val


def value_for_key_path(iterable, key_path, map=None, skip=[None], default=None):
    if not bool(iterable):
        return default
    if not bool(key_path):
        return default
    last_key = key_path.pop()
    val = iterable
    for key in key_path:
        if not isinstance(val, (Sequence, Mapping)) or isinstance(val, (str, bytes)) or key not in val:
            return default
        val = val[key]
    return value_for_key(val, last_key, map=map, skip=skip, default=default)


def value_for_any_key(d: dict, keys: List[str], skip=[None], map=None, default=None):
    if d is None:
        return default
    val = default
    for k in keys:
        if not isinstance(k, (str, bytes)) and isinstance(k, Sequence):
            # Key path
            x = value_for_key_path(d, k, skip=[])
            if x in skip:
                continue
            if callable(map):
                x = map(x)
            val = x
            break
        elif k in d:
            x = d[k]
            if x in skip:
                continue
            if callable(map):
                x = map(x)
            val = x
            break
    return val


def allclose(a: Iterable, b: Iterable, rtol=1.e-5, atol=1.e-8, equal_nan=False):
    return np.allclose(a, b, rtol=rtol, atol=atol, equal_nan=equal_nan)
