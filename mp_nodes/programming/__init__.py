"""ProgrammingNode — abstract programming primitives organized by category."""

from mp_nodes._base import ANY, MegaPackNodeBase, OpRegistry

REGISTRY = OpRegistry()
op = REGISTRY.register

from mp_nodes.programming.operations import (  # noqa: E402, F401
    encoding,
    logic_bits,
    math_signals,
    text,
    data_struct,
    control_flow,
    crypto,
)


class ProgrammingNode(MegaPackNodeBase):
    REGISTRY = REGISTRY
    RETURN_TYPES = ("STRING", "INT", "FLOAT", "BOOLEAN", "LIST", "DICT", ANY)
    RETURN_NAMES = ("string", "int", "float", "bool", "list", "dict", "any")
