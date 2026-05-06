"""Tests for MegaPackNodeBase.process — the per-execution dispatcher."""

import pytest

from nodes._base import MegaPackNodeBase, OpRegistry


def _make_one_op_node():
    reg = OpRegistry()

    @reg.register(
        op_id="echo",
        display_name="Echo",
        category="Test",
        input_schema={"required": {"text": ("STRING", {"default": ""})}},
        output_indices=(0,),
    )
    def echo(self, text):
        return (text,)

    class _N(MegaPackNodeBase):
        REGISTRY = reg
        RETURN_TYPES = ("STRING", "INT")
        RETURN_NAMES = ("string", "int")

    return _N


def test_process_dispatches_to_registered_op():
    NodeCls = _make_one_op_node()
    result = NodeCls().process(mode="echo", theme="(use pack default)", text="hello")
    assert result[0] == "hello"


def test_process_pads_unfilled_outputs():
    NodeCls = _make_one_op_node()
    result = NodeCls().process(mode="echo", theme="(use pack default)", text="hi")
    assert result == ("hi", 0)


def test_process_ignores_theme_argument():
    """The theme widget is UI-only; Python side just accepts and ignores it."""
    NodeCls = _make_one_op_node()
    result = NodeCls().process(mode="echo", theme="cyberpunk", text="x")
    assert result[0] == "x"


def test_process_unknown_mode_raises_runtime_error():
    NodeCls = _make_one_op_node()
    with pytest.raises(RuntimeError, match="unknown mode"):
        NodeCls().process(mode="not_a_real_mode", theme="(use pack default)", text="x")


def test_process_wraps_op_exceptions_with_context():
    reg = OpRegistry()

    @reg.register(
        op_id="boom",
        display_name="Boom",
        category="Test",
        input_schema={},
        output_indices=(),
    )
    def boom(self):
        raise ValueError("inner kaboom")

    class _N(MegaPackNodeBase):
        REGISTRY = reg
        RETURN_TYPES = ("STRING",)
        RETURN_NAMES = ("string",)

    with pytest.raises(RuntimeError, match=r"\[_N/boom\] inner kaboom"):
        _N().process(mode="boom", theme="(use pack default)")
