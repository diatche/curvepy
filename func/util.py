import inspect
from typing import Mapping, Iterable


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


def extend(primary: Mapping, *others: Mapping, in_place=False):
    """
    Copies values from `others` to `primary`.
    """
    others = flatten(others)
    if not in_place:
        primary = dict(primary or {})
    for other in others:
        if other is None:
            continue
        for key, value in other.items():
            primary[key] = value
    return primary


def count_positional_args(f, default=1):
    if not callable(f):
        raise Exception('Expected callable function')
    if inspect.isbuiltin(f):
        return default
    sig = inspect.signature(f)
    count = 0
    for param in sig.parameters.values():
        if param.kind == inspect.Parameter.POSITIONAL_ONLY or \
            param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD:
            count += 1
    return count
