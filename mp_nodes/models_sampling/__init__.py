"""ModelsSamplingNode — model intel, resolution helpers, seed/sampler ops."""

from mp_nodes._base import MegaPackNodeBase, OpRegistry

REGISTRY = OpRegistry()
op = REGISTRY.register

from mp_nodes.models_sampling.operations import (  # noqa: E402, F401
    model_intel,
    resolution,
    seed_sampling,
)


class ModelsSamplingNode(MegaPackNodeBase):
    REGISTRY = REGISTRY
    RETURN_TYPES = ("MODEL", "CLIP", "VAE", "STRING", "STRING", "INT", "INT", "FLOAT", "DICT")
    RETURN_NAMES = ("model", "clip", "vae", "name", "sampler", "seed", "dim", "cfg", "params")
