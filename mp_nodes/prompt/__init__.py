"""PromptNode — prompt-engineering operations."""

from mp_nodes._base import MegaPackNodeBase, OpRegistry

REGISTRY = OpRegistry()
op = REGISTRY.register

from mp_nodes.prompt.operations import prompt  # noqa: E402, F401


class PromptNode(MegaPackNodeBase):
    REGISTRY = REGISTRY
    RETURN_TYPES = ("STRING", "STRING", "LIST", "INT")
    RETURN_NAMES = ("prompt", "negative", "all_prompts", "token_count")
