"""ConvenienceNode — reroute, switch, gate, counter, timer, debug, presets, compare."""

from nodes._base import ANY, MegaPackNodeBase, OpRegistry

REGISTRY = OpRegistry()
op = REGISTRY.register

from nodes.convenience.operations import convenience  # noqa: E402, F401


class ConvenienceNode(MegaPackNodeBase):
    REGISTRY = REGISTRY
    RETURN_TYPES = (ANY, ANY, ANY, ANY, ANY)
    RETURN_NAMES = ("out_1", "out_2", "out_3", "out_4", "out_5")
