"""ComfyUI-Utility-MegaPack — entry point.

ComfyUI imports this module and reads NODE_CLASS_MAPPINGS,
NODE_DISPLAY_NAME_MAPPINGS, and WEB_DIRECTORY.
"""

# ComfyUI loads custom nodes via spec_from_file_location, which does NOT add
# the package's own directory to sys.path. Inject the package directory once at
# import time. We use `mp_*` prefixed package names so this injection cannot
# shadow ComfyUI core's `nodes` module (which is what broke v0.1.1).
import os as _os
import sys as _sys
_HERE = _os.path.dirname(_os.path.abspath(__file__))
if _HERE not in _sys.path:
    _sys.path.insert(0, _HERE)

from mp_nodes.smoke import SmokeTestNode
from mp_nodes.programming import ProgrammingNode
from mp_nodes.prompt import PromptNode
from mp_nodes.image_pro import ImageProNode
from mp_nodes.mask_latent import MaskLatentNode
from mp_nodes.io_workflow import IOWorkflowNode
from mp_nodes.convenience import ConvenienceNode
from mp_nodes.models_sampling import ModelsSamplingNode

NODE_CLASS_MAPPINGS: dict = {
    "UtilMegaPack_SmokeTest": SmokeTestNode,
    "UtilMegaPack_Programming": ProgrammingNode,
    "UtilMegaPack_Prompt": PromptNode,
    "UtilMegaPack_ImagePro": ImageProNode,
    "UtilMegaPack_MaskLatent": MaskLatentNode,
    "UtilMegaPack_IOWorkflow": IOWorkflowNode,
    "UtilMegaPack_Convenience": ConvenienceNode,
    "UtilMegaPack_ModelsSampling": ModelsSamplingNode,
}

NODE_DISPLAY_NAME_MAPPINGS: dict = {
    "UtilMegaPack_SmokeTest": "Smoke Test",
    "UtilMegaPack_Programming": "Programming",
    "UtilMegaPack_Prompt": "Prompt",
    "UtilMegaPack_ImagePro": "Image Pro",
    "UtilMegaPack_MaskLatent": "Mask & Latent",
    "UtilMegaPack_IOWorkflow": "IO & Workflow",
    "UtilMegaPack_Convenience": "Convenience",
    "UtilMegaPack_ModelsSampling": "Models & Sampling",
}

WEB_DIRECTORY = "./web"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
