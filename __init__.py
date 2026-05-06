"""ComfyUI-Utility-MegaPack — entry point.

ComfyUI imports this module and reads NODE_CLASS_MAPPINGS,
NODE_DISPLAY_NAME_MAPPINGS, and WEB_DIRECTORY.
"""

from nodes.smoke import SmokeTestNode
from nodes.programming import ProgrammingNode
from nodes.prompt import PromptNode

NODE_CLASS_MAPPINGS: dict = {
    "UtilMegaPack_SmokeTest": SmokeTestNode,
    "UtilMegaPack_Programming": ProgrammingNode,
    "UtilMegaPack_Prompt": PromptNode,
}

NODE_DISPLAY_NAME_MAPPINGS: dict = {
    "UtilMegaPack_SmokeTest": "Smoke Test",
    "UtilMegaPack_Programming": "Programming",
    "UtilMegaPack_Prompt": "Prompt",
}

WEB_DIRECTORY = "./web"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
