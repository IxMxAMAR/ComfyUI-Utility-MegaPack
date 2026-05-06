"""Smoke-level test for the ProgrammingNode skeleton."""

from nodes.programming import ProgrammingNode


def test_programming_node_has_seven_outputs():
    assert len(ProgrammingNode.RETURN_TYPES) == 7
    assert ProgrammingNode.RETURN_TYPES[:6] == ("STRING", "INT", "FLOAT", "BOOLEAN", "LIST", "DICT")


def test_programming_node_input_types_lists_smoke_op():
    schema = ProgrammingNode.INPUT_TYPES()
    options, _ = schema["required"]["mode"]
    assert "_skeleton_check" in options


def test_programming_node_smoke_op_round_trips():
    result = ProgrammingNode().process(
        mode="_skeleton_check", theme="(use pack default)", value="round-trip"
    )
    assert result[0] == "round-trip"
