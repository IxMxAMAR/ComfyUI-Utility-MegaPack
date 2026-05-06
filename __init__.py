"""ComfyUI-Utility-MegaPack — entry point.

ComfyUI imports this module and reads NODE_CLASS_MAPPINGS,
NODE_DISPLAY_NAME_MAPPINGS, and WEB_DIRECTORY.
"""

from nodes.smoke import SmokeTestNode
from nodes.programming import ProgrammingNode
from nodes.prompt import PromptNode
from nodes.image_pro import ImageProNode
from nodes.mask_latent import MaskLatentNode
from nodes.io_workflow import IOWorkflowNode
from nodes.convenience import ConvenienceNode

NODE_CLASS_MAPPINGS: dict = {
    "UtilMegaPack_SmokeTest": SmokeTestNode,
    "UtilMegaPack_Programming": ProgrammingNode,
    "UtilMegaPack_Prompt": PromptNode,
    "UtilMegaPack_ImagePro": ImageProNode,
    "UtilMegaPack_MaskLatent": MaskLatentNode,
    "UtilMegaPack_IOWorkflow": IOWorkflowNode,
    "UtilMegaPack_Convenience": ConvenienceNode,
}

NODE_DISPLAY_NAME_MAPPINGS: dict = {
    "UtilMegaPack_SmokeTest": "Smoke Test",
    "UtilMegaPack_Programming": "Programming",
    "UtilMegaPack_Prompt": "Prompt",
    "UtilMegaPack_ImagePro": "Image Pro",
    "UtilMegaPack_MaskLatent": "Mask & Latent",
    "UtilMegaPack_IOWorkflow": "IO & Workflow",
    "UtilMegaPack_Convenience": "Convenience",
}

WEB_DIRECTORY = "./web"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
