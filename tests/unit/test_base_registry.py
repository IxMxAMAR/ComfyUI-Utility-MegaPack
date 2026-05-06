"""Tests for OpRegistry — per-node operation registry."""

import pytest

from nodes._base import OpRegistry


def test_register_stores_op_by_id():
    reg = OpRegistry()

    @reg.register(
        op_id="echo",
        display_name="Echo",
        category="Test",
        input_schema={"required": {"text": ("STRING", {})}},
        output_indices=(0,),
    )
    def echo(self, text):
        return (text,)

    assert "echo" in reg.ops
    assert reg.ops["echo"].op_id == "echo"
    assert reg.ops["echo"].callable is echo


def test_register_returns_undecorated_callable():
    """The decorator must return the original callable so users can still call it directly."""
    reg = OpRegistry()

    @reg.register(
        op_id="x",
        display_name="X",
        category="Test",
        input_schema={},
        output_indices=(),
    )
    def x(self):
        return ("ok",)

    assert x.__name__ == "x"
    assert x(None) == ("ok",)


def test_register_rejects_duplicate_op_id():
    reg = OpRegistry()

    @reg.register(op_id="dup", display_name="A", category="C", input_schema={}, output_indices=())
    def a(self):
        return ()

    with pytest.raises(ValueError, match="duplicate op_id"):

        @reg.register(op_id="dup", display_name="B", category="C", input_schema={}, output_indices=())
        def b(self):
            return ()


def test_categories_returns_sorted_unique():
    reg = OpRegistry()

    @reg.register(op_id="a", display_name="A", category="Zeta", input_schema={}, output_indices=())
    def a(self): return ()

    @reg.register(op_id="b", display_name="B", category="Alpha", input_schema={}, output_indices=())
    def b(self): return ()

    @reg.register(op_id="c", display_name="C", category="Alpha", input_schema={}, output_indices=())
    def c(self): return ()

    assert reg.categories() == ["Alpha", "Zeta"]


def test_ops_in_filters_by_category():
    reg = OpRegistry()

    @reg.register(op_id="a", display_name="A", category="X", input_schema={}, output_indices=())
    def a(self): return ()

    @reg.register(op_id="b", display_name="B", category="Y", input_schema={}, output_indices=())
    def b(self): return ()

    x_ops = reg.ops_in("X")
    assert len(x_ops) == 1
    assert x_ops[0].op_id == "a"


def test_all_op_ids_returns_sorted():
    reg = OpRegistry()

    @reg.register(op_id="zebra", display_name="Z", category="C", input_schema={}, output_indices=())
    def z(self): return ()

    @reg.register(op_id="apple", display_name="A", category="C", input_schema={}, output_indices=())
    def a(self): return ()

    assert reg.all_op_ids() == ["apple", "zebra"]
