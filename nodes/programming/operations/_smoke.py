"""Skeleton-verification op. Removed once category ops land."""
from .. import op


@op(
    op_id="_skeleton_check",
    display_name="(skeleton check)",
    category="_meta",
    input_schema={"required": {"value": ("STRING", {"default": "ok"})}},
    output_indices=(0,),
    description="Returns the input string. Verifies the package skeleton.",
)
def skeleton_check(self, value):
    return (value,)
