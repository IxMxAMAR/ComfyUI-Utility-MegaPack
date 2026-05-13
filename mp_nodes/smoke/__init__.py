"""Smoke node — exists only to verify the registration pipeline end-to-end."""

from mp_nodes._base import MegaPackNodeBase, OpRegistry

REGISTRY = OpRegistry()
op = REGISTRY.register

# Trigger op registration. `op` must be bound before this import — Python
# caches the partially-initialized module so `from nodes.smoke import op`
# inside echo.py finds the already-defined name.
from mp_nodes.smoke.operations import echo  # noqa: E402, F401


class SmokeTestNode(MegaPackNodeBase):
    REGISTRY = REGISTRY
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text",)
