"""MaskLatentNode — mask + latent operations."""

from nodes._base import MegaPackNodeBase, OpRegistry

REGISTRY = OpRegistry()
op = REGISTRY.register

from nodes.mask_latent.operations import mask_ops, latent_ops  # noqa: E402, F401


class MaskLatentNode(MegaPackNodeBase):
    REGISTRY = REGISTRY
    RETURN_TYPES = ("MASK", "LATENT", "DICT")
    RETURN_NAMES = ("mask", "latent", "info")
