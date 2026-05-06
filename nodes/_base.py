"""Base class, registry, and shared types for Utility-MegaPack nodes."""


class AnyType(str):
    """ComfyUI wildcard type.

    ComfyUI compares socket types with `!=`; returning False from `__ne__`
    makes this type compatible with anything. Standard pattern in the
    custom-node ecosystem.
    """

    def __ne__(self, other: object) -> bool:
        return False


ANY = AnyType("*")
