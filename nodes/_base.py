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


class OutputNotProducedError(RuntimeError):
    """Raised when a workflow wires an opaque output (MODEL/CLIP/VAE) that the active mode does not produce."""

    def __init__(self, *, slot_name: str, op_id: str) -> None:
        self.slot_name = slot_name
        self.op_id = op_id
        super().__init__(
            f"Operation '{op_id}' does not produce a '{slot_name}' output — "
            f"disconnect that slot or pick a different mode."
        )


def _default_for_type(type_name: str, op_id: str):
    """Return a type-appropriate default for an unfilled output slot.

    Lazy-imports torch so this module can be imported in tooling environments
    where torch isn't installed (e.g. doc-generation pipelines).
    """
    if isinstance(type_name, AnyType):
        return None
    if type_name == "STRING":
        return ""
    if type_name == "INT":
        return 0
    if type_name == "FLOAT":
        return 0.0
    if type_name == "BOOLEAN":
        return False
    if type_name == "LIST":
        return []
    if type_name == "DICT":
        return {}
    if type_name in ("MODEL", "CLIP", "VAE"):
        raise OutputNotProducedError(slot_name=type_name, op_id=op_id)
    if type_name == "IMAGE":
        import torch

        return torch.zeros((1, 1, 1, 3))
    if type_name == "MASK":
        import torch

        return torch.zeros((1, 1, 1))
    if type_name == "LATENT":
        import torch

        return {"samples": torch.zeros((1, 4, 8, 8))}
    return None


def _pad_outputs(
    *,
    op_result: tuple,
    output_indices: tuple,
    return_types: tuple,
    op_id: str,
) -> tuple:
    """Pad an op's result tuple to the full RETURN_TYPES width.

    Filled slots come from `op_result` in the order given by `output_indices`.
    Unfilled slots get type-appropriate defaults from `_default_for_type`.
    Opaque types (MODEL/CLIP/VAE) raise OutputNotProducedError if unfilled.
    """
    out = [None] * len(return_types)
    for idx, value in zip(output_indices, op_result):
        out[idx] = value
    filled = set(output_indices)
    for i, type_name in enumerate(return_types):
        if i not in filled:
            out[i] = _default_for_type(type_name, op_id=op_id)
    return tuple(out)
