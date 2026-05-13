"""Tests for the Math & Signals category."""

import pytest

from mp_nodes.programming import ProgrammingNode


def run(mode, **kwargs):
    return ProgrammingNode().process(mode=mode, theme="(use pack default)", **kwargs)


def test_math_add():
    assert run("math_add", a=2.0, b=3.0)[2] == 5.0


def test_math_subtract():
    assert run("math_subtract", a=10.0, b=4.0)[2] == 6.0


def test_math_multiply():
    assert run("math_multiply", a=3.0, b=4.0)[2] == 12.0


def test_math_divide():
    assert run("math_divide", a=10.0, b=4.0)[2] == 2.5


def test_math_divide_by_zero_raises():
    with pytest.raises(RuntimeError, match=r"\[ProgrammingNode/math_divide\] division by zero"):
        run("math_divide", a=1.0, b=0.0)


def test_math_clamp_above():
    assert run("math_clamp", value=10.0, lo=0.0, hi=5.0)[2] == 5.0


def test_math_clamp_below():
    assert run("math_clamp", value=-1.0, lo=0.0, hi=5.0)[2] == 0.0


def test_math_clamp_inside():
    assert run("math_clamp", value=2.5, lo=0.0, hi=5.0)[2] == 2.5


def test_math_lerp_endpoints():
    assert run("math_lerp", a=0.0, b=10.0, t=0.0)[2] == 0.0
    assert run("math_lerp", a=0.0, b=10.0, t=1.0)[2] == 10.0


def test_math_lerp_midpoint():
    assert run("math_lerp", a=0.0, b=10.0, t=0.5)[2] == 5.0


def test_stats_mean_basic():
    assert run("stats_mean", values=[1, 2, 3, 4])[2] == 2.5


def test_stats_mean_empty():
    assert run("stats_mean", values=[])[2] == 0.0


def test_stats_median_odd_count():
    assert run("stats_median", values=[1, 2, 3])[2] == 2.0


def test_stats_median_even_count():
    assert run("stats_median", values=[1, 2, 3, 4])[2] == 2.5


def test_stats_std_population():
    # values = [2, 4, 4, 4, 5, 5, 7, 9], pstdev = 2.0
    assert run("stats_std", values=[2, 4, 4, 4, 5, 5, 7, 9])[2] == pytest.approx(2.0)


def test_stats_std_single_value_returns_zero():
    assert run("stats_std", values=[5])[2] == 0.0


def test_random_uniform_seeded_is_deterministic():
    a = run("random_uniform", lo=0.0, hi=1.0, seed=42)[2]
    b = run("random_uniform", lo=0.0, hi=1.0, seed=42)[2]
    assert a == b


def test_random_uniform_in_range():
    v = run("random_uniform", lo=2.0, hi=5.0, seed=7)[2]
    assert 2.0 <= v <= 5.0
