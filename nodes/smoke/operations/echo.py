"""Echo — return the input string unchanged. Smoke-test op."""

from nodes.smoke import op


@op(
    op_id="echo",
    display_name="Echo",
    category="Test",
    input_schema={
        "required": {
            "text": ("STRING", {"default": "hello"}),
        },
    },
    output_indices=(0,),
    description="Return the input string unchanged.",
)
def echo(self, text):
    return (text,)
