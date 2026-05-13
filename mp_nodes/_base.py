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
            # Reserved widget names — collide with `process(mode=..., theme=...)`
            # framework kwargs and surface as cryptic "multiple values for
            # argument 'mode'" runtime errors (Gemini review #8). Catch at
            # registration time so op authors get a clear failure mode.
            for section in ("required", "optional"):
                for reserved in ("mode", "theme"):
                    if reserved in input_schema.get(section, {}):
                        raise ValueError(
                            f"op '{op_id}': widget name '{reserved}' is reserved "
                            f"(collides with the framework's `mode`/`theme` kwargs). "
                            f"Pick a different widget name (e.g. '{reserved}_kind')."
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
        # Opaque types — return None and let ComfyUI's runtime raise a clear error
        # at the wiring level if a downstream node tries to use None as a model.
        # We don't have visibility into which output sockets are wired at this
        # layer, so eager raising here would break valid workflows that produce
        # only the non-opaque outputs.
        return None
    if type_name == "IMAGE":
        import torch

        return torch.zeros((1, 1, 1, 3))
    if type_name == "MASK":
        import torch

        return torch.zeros((1, 1, 1))
    if type_name == "LATENT":
        # Empty dict, NOT a hardcoded 4-channel zero latent. Flux/SD3/etc.
        # use 16 channels, so the old default would cause cryptic shape
        # mismatches downstream (Gemini review #6). Downstream nodes that
        # need samples will raise a clear "missing 'samples'" error instead.
        return {}
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
    Opaque types (MODEL/CLIP/VAE) pad to None — ComfyUI's runtime then surfaces
    a clear error at the wire level if a downstream node tries to use None.
    LATENT pads to {} for the same reason (avoid wrong-channel-count crashes).
    """
    for idx in output_indices:
        if idx >= len(return_types):
            raise ValueError(
                f"[{op_id}] output_indices={output_indices!r} is out of range "
                f"for RETURN_TYPES of length {len(return_types)}"
            )
    out = [None] * len(return_types)
    for idx, value in zip(output_indices, op_result):
        out[idx] = value
    filled = set(output_indices)
    for i, type_name in enumerate(return_types):
        if i not in filled:
            out[i] = _default_for_type(type_name, op_id=op_id)
    return tuple(out)


THEME_CHOICES: list[str] = [
    "(use pack default)",
    "(use ComfyUI default)",
    "cyberpunk",
    "minimalist",
    "glassmorphic",
    "retro_terminal",
    "default",
    "holographic",
    "paper_ink",
    "brutalist",
    "solarized_dark",
    "dracula",
    "high_contrast",
]


class MegaPackNodeBase:
    """Shared base class for all Utility-MegaPack node classes.

    Subclasses must set:
      - REGISTRY: an OpRegistry instance
      - RETURN_TYPES: tuple of ComfyUI output type names
      - RETURN_NAMES: tuple of socket display names
    """

    REGISTRY: OpRegistry = None  # type: ignore[assignment]
    RETURN_TYPES: tuple = ()
    RETURN_NAMES: tuple = ()
    FUNCTION = "process"
    CATEGORY = "Utility-MegaPack"

    @classmethod
    def INPUT_TYPES(cls) -> dict:
        if cls.REGISTRY is None:
            raise RuntimeError(f"{cls.__name__}.REGISTRY is not set")

        op_ids = cls.REGISTRY.all_op_ids()
        if not op_ids:
            raise RuntimeError(f"{cls.__name__}.REGISTRY has no registered operations")

        required: dict = {"mode": (op_ids, {"default": op_ids[0]})}
        optional: dict = {}

        for op in cls.REGISTRY.ops.values():
            for section_key in ("required", "optional"):
                for widget_name, widget_def in op.input_schema.get(section_key, {}).items():
                    # Per-op widgets all live in optional. JS hides the irrelevant ones per mode.
                    if widget_name not in optional:
                        optional[widget_name] = widget_def

        # Theme widget last in required.
        required["theme"] = (THEME_CHOICES, {"default": "(use pack default)"})

        return {"required": required, "optional": optional}

    def process(self, *, mode: str, theme: str, **op_inputs) -> tuple:
        """Dispatch to the registered op identified by `mode`.

        `theme` is accepted for ComfyUI widget-binding but ignored on the Python side
        — themes are applied client-side by the JS theme engine.
        """
        op = self.REGISTRY.ops.get(mode)
        if op is None:
            raise RuntimeError(
                f"unknown mode '{mode}' on {type(self).__name__} "
                f"(registered: {self.REGISTRY.all_op_ids()})"
            )

        try:
            op_result = op.callable(self, **op_inputs)
        except OutputNotProducedError:
            raise
        except Exception as exc:
            raise RuntimeError(
                f"[{type(self).__name__}/{op.op_id}] {exc}"
            ) from exc

        return _pad_outputs(
            op_result=op_result,
            output_indices=op.output_indices,
            return_types=self.RETURN_TYPES,
            op_id=op.op_id,
        )
