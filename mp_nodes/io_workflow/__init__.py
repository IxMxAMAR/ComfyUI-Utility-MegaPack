"""IOWorkflowNode — filesystem, HTTP, save-with-manifest, sweeps, monitors."""

from mp_nodes._base import MegaPackNodeBase, OpRegistry

REGISTRY = OpRegistry()
op = REGISTRY.register

from mp_nodes.io_workflow.operations import (  # noqa: E402, F401
    filesystem,
    network,
    workflow,
    system,
)


class IOWorkflowNode(MegaPackNodeBase):
    REGISTRY = REGISTRY
    RETURN_TYPES = ("STRING", "DICT", "IMAGE", "INT")
    RETURN_NAMES = ("text", "parsed", "image", "status_code")
