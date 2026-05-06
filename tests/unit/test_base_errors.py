"""Tests for OutputNotProducedError — raised when opaque-type slots are wired but unfilled."""

from nodes._base import OutputNotProducedError


def test_error_is_runtime_error_subclass():
    assert issubclass(OutputNotProducedError, RuntimeError)


def test_error_message_includes_slot_name_and_op_id():
    err = OutputNotProducedError(slot_name="model", op_id="for_loop")
    assert "model" in str(err)
    assert "for_loop" in str(err)


def test_error_attributes_are_accessible():
    err = OutputNotProducedError(slot_name="clip", op_id="echo")
    assert err.slot_name == "clip"
    assert err.op_id == "echo"
