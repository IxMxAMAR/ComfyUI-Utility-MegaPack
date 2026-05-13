"""Tests for OpDef — the dataclass that describes one registered operation."""

from mp_nodes._base import OpDef


def _noop(self):
    return ()


def test_opdef_construction_with_required_fields():
    op = OpDef(
        op_id="echo",
        display_name="Echo",
        category="Test",
        callable=_noop,
        input_schema={"required": {"text": ("STRING", {"default": ""})}},
        output_indices=(0,),
    )
    assert op.op_id == "echo"
    assert op.display_name == "Echo"
    assert op.category == "Test"
    assert op.callable is _noop
    assert op.output_indices == (0,)
    assert op.description == ""


def test_opdef_description_is_optional():
    op = OpDef(
        op_id="x",
        display_name="X",
        category="Test",
        callable=_noop,
        input_schema={},
        output_indices=(),
        description="example op",
    )
    assert op.description == "example op"


def test_opdef_input_schema_defaults_to_empty_dict():
    op = OpDef(
        op_id="x",
        display_name="X",
        category="Test",
        callable=_noop,
        input_schema={},
        output_indices=(),
    )
    assert op.input_schema == {}
