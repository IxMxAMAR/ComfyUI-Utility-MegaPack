"""ImageProNode — image loaders + modifications + inspectors."""

from nodes._base import MegaPackNodeBase, OpRegistry

REGISTRY = OpRegistry()
op = REGISTRY.register

from nodes.image_pro.operations import (  # noqa: E402, F401
    load,
    value_ops,
    spatial_ops,
    style_ops,
    inspect,
)


class ImageProNode(MegaPackNodeBase):
    REGISTRY = REGISTRY
    RETURN_TYPES = ("IMAGE", "MASK", "INT", "INT", "STRING")
    RETURN_NAMES = ("image", "mask", "width", "height", "metadata_json")
