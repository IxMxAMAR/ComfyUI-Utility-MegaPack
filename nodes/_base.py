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


class OpRegistry:
    """Per-node operation registry. Supports decorator-style registration."""

    def __init__(self) -> None:
        self.ops: dict[str, OpDef] = {}

    def register(
        self,
        *,
        op_id: str,
        display_name: str,
        category: str,
        input_schema: dict,
        output_indices: tuple,
        description: str = "",
    ) -> Callable[[Callable], Callable]:
        """Decorator that registers a function as an operation on this registry."""

        def decorator(fn: Callable) -> Callable:
            if op_id in self.ops:
                raise ValueError(
                    f"duplicate op_id '{op_id}' (already registered as '{self.ops[op_id].display_name}')"
                )
            self.ops[op_id] = OpDef(
                op_id=op_id,
                display_name=display_name,
                category=category,
                callable=fn,
                input_schema=input_schema,
                output_indices=output_indices,
                description=description,
            )
            return fn

        return decorator

    def categories(self) -> list[str]:
        return sorted({op.category for op in self.ops.values()})

    def ops_in(self, category: str) -> list[OpDef]:
        return [op for op in self.ops.values() if op.category == category]

    def all_op_ids(self) -> list[str]:
        return sorted(self.ops.keys())
