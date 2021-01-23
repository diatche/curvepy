import pytest
from pytest import approx
from func.sin import Sin


def test_with_sin():
    sin_original = Sin(amplitude=1, period=4)
    sin_extended = sin_original.subset((0, 4)).extension(
        'sin',
        period=4,
        start=True,
        end=True,
        min_step=1e-4
    )

    assert sin_original(-1) == approx(sin_extended(-1), rel=0.01)
    assert sin_original(-0.1) == approx(sin_extended(-0.1), rel=0.01)
    assert sin_original(0) == approx(sin_extended(0), rel=0.01)
    assert sin_original(4) == approx(sin_extended(4), rel=0.01)
    assert sin_original(4.1) == approx(sin_extended(4.1), rel=0.01)
    assert sin_original(5) == approx(sin_extended(5), rel=0.01)


def test_regression():
    sin_original = Sin(amplitude=1, period=4)
    sin_extended = sin_original.subset((0, 4)).extension(
        'sin',
        period=4,
        regression_degree=10,
        start=True,
        end=True,
        min_step=1e-4
    )

    assert sin_original(-1) == approx(sin_extended(-1), rel=0.01)
    assert sin_original(-0.1) == approx(sin_extended(-0.1), rel=0.01)
    assert sin_original(0) == approx(sin_extended(0), rel=0.01)
    assert sin_original(4) == approx(sin_extended(4), rel=0.01)
    assert sin_original(4.1) == approx(sin_extended(4.1), rel=0.01)
    assert sin_original(5) == approx(sin_extended(5), rel=0.01)
