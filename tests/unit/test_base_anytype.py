"""Tests for the AnyType wildcard used to mark wildcard ComfyUI sockets."""

from mp_nodes._base import ANY, AnyType


def test_anytype_is_string_subclass():
    assert isinstance(ANY, str)
    assert ANY == "*"


def test_anytype_ne_returns_false_for_anything():
    """ComfyUI uses != to detect type mismatch; AnyType must always say 'no mismatch'."""
    assert (ANY != "STRING") is False
    assert (ANY != "IMAGE") is False
    assert (ANY != "MASK") is False
    assert (ANY != "INT") is False
    assert (ANY != ANY) is False


def test_anytype_class_can_be_instantiated_directly():
    custom = AnyType("anything")
    assert (custom != "FOO") is False
