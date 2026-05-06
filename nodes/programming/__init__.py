"""ProgrammingNode — abstract programming primitives organized by category."""

from nodes._base import ANY, MegaPackNodeBase, OpRegistry

REGISTRY = OpRegistry()
op = REGISTRY.register

from nodes.programming.operations import (  # noqa: E402, F401
    _smoke,
    encoding,
    logic_bits,
    math_signals,
)


class ProgrammingNode(MegaPackNodeBase):
    REGISTRY = REGISTRY
    RETURN_TYPES = ("STRING", "INT", "FLOAT", "BOOLEAN", "LIST", "DICT", ANY)
    RETURN_NAMES = ("string", "int", "float", "bool", "list", "dict", "any")
