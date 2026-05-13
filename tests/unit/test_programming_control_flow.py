"""Tests for the Control Flow category."""

import pytest

from mp_nodes.programming import ProgrammingNode


def run(mode, **kwargs):
    return ProgrammingNode().process(mode=mode, theme="(use pack default)", **kwargs)


class TestForLoop:
    def test_basic(self):
        assert run("for_loop", start=0, end=5, step=1)[4] == [0, 1, 2, 3, 4]

    def test_step_2(self):
        assert run("for_loop", start=0, end=10, step=2)[4] == [0, 2, 4, 6, 8]


class TestWhileLoop:
    def test_simple_counter(self):
        out = run("while_loop", expr="i<5", max_iters=100)[4]
        assert out == [0, 1, 2, 3, 4]

    def test_max_iters_caps(self):
        out = run("while_loop", expr="i<999999", max_iters=10)[4]
        assert len(out) == 10

    def test_dunder_in_expr_raises(self):
        with pytest.raises(RuntimeError, match="forbidden '__'"):
            run("while_loop", expr="i.__class__", max_iters=10)


class TestIfElse:
    def test_true(self):
        assert run("if_else", condition=True, when_true="yes", when_false="no")[0] == "yes"

    def test_false(self):
        assert run("if_else", condition=False, when_true="yes", when_false="no")[0] == "no"


class TestCompare:
    def test_lt_true(self):
        assert run("compare", a=1.0, op="<", b=2.0)[3] is True

    def test_eq_true(self):
        assert run("compare", a=2.0, op="==", b=2.0)[3] is True

    def test_ne_true(self):
        assert run("compare", a=1.0, op="!=", b=2.0)[3] is True

    def test_unknown_op_raises(self):
        with pytest.raises(RuntimeError, match="unknown compare op"):
            run("compare", a=1.0, op="xx", b=2.0)


class TestEvalExpr:
    def test_basic_arithmetic(self):
        assert run("eval_expr", expr="2 + 3 * 4", vars_json="{}")[6] == 14

    def test_with_vars(self):
        assert run("eval_expr", expr="x * y", vars_json='{"x": 3, "y": 4}')[6] == 12

    def test_dunder_blocked(self):
        with pytest.raises(RuntimeError, match="forbidden '__'"):
            run("eval_expr", expr="x.__class__", vars_json='{"x": 1}')

    def test_undefined_name_raises(self):
        with pytest.raises(RuntimeError, match="undefined name"):
            run("eval_expr", expr="undefined_var + 1", vars_json="{}")


class TestNullCoalesce:
    def test_a_wins_when_present(self):
        assert run("null_coalesce", a="first", b="second", c="third")[0] == "first"

    def test_b_wins_when_a_empty(self):
        assert run("null_coalesce", a="", b="second", c="third")[0] == "second"

    def test_c_wins_when_a_b_empty(self):
        assert run("null_coalesce", a="", b="", c="third")[0] == "third"

    def test_all_empty_returns_empty(self):
        assert run("null_coalesce", a="", b="", c="")[0] == ""


class TestSwitchCase:
    def test_known_case(self):
        out = run("switch_case", value="apple", cases_json='{"apple":"red","banana":"yellow"}')[0]
        assert out == "red"

    def test_unknown_falls_to_default(self):
        out = run("switch_case", value="grape", cases_json='{"apple":"red","_":"unknown"}')[0]
        assert out == "unknown"

    def test_no_default_returns_empty_string(self):
        out = run("switch_case", value="grape", cases_json='{"apple":"red"}')[0]
        assert out == ""
