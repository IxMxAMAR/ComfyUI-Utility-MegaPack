"""Base class, registry, and shared types for Utility-MegaPack nodes."""

from dataclasses import dataclass
from typing import Callable


class AnyType(str):
    """ComfyUI wildcard type.

    ComfyUI compares socket types with `!=`; returning False from `__ne__`
    makes this type compatible with anything. Standard pattern in the
    custom-node ecosystem.
    """

    def __ne__(self, other: object) -> bool:
        return False


ANY = AnyType("*")


@dataclass
class OpDef:
    """One registered operation on a node."""

    op_id: str
    display_name: str
    category: str
    callable: Callable
    input_schema: dict
    output_indices: tuple
    description: str = ""
