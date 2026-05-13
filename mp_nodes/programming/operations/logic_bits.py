"""Boolean and bitwise operations."""

from .. import op


@op(
    op_id="bool_and",
    display_name="Boolean AND",
    category="Logic & Bits",
    input_schema={"required": {
        "a": ("BOOLEAN", {"default": False}),
        "b": ("BOOLEAN", {"default": False}),
    }},
    output_indices=(3,),
)
def bool_and(self, a, b):
    return (bool(a) and bool(b),)


@op(
    op_id="bool_or",
    display_name="Boolean OR",
    category="Logic & Bits",
    input_schema={"required": {
        "a": ("BOOLEAN", {"default": False}),
        "b": ("BOOLEAN", {"default": False}),
    }},
    output_indices=(3,),
)
def bool_or(self, a, b):
    return (bool(a) or bool(b),)


@op(
    op_id="bool_not",
    display_name="Boolean NOT",
    category="Logic & Bits",
    input_schema={"required": {"a": ("BOOLEAN", {"default": False})}},
    output_indices=(3,),
)
def bool_not(self, a):
    return (not bool(a),)


@op(
    op_id="bool_xor",
    display_name="Boolean XOR",
    category="Logic & Bits",
    input_schema={"required": {
        "a": ("BOOLEAN", {"default": False}),
        "b": ("BOOLEAN", {"default": False}),
    }},
    output_indices=(3,),
)
def bool_xor(self, a, b):
    return (bool(a) != bool(b),)


@op(
    op_id="bitwise_and",
    display_name="Bitwise AND",
    category="Logic & Bits",
    input_schema={"required": {
        "a": ("INT", {"default": 0}),
        "b": ("INT", {"default": 0}),
    }},
    output_indices=(1,),
)
def bitwise_and(self, a, b):
    return (int(a) & int(b),)


@op(
    op_id="bitwise_or",
    display_name="Bitwise OR",
    category="Logic & Bits",
    input_schema={"required": {
        "a": ("INT", {"default": 0}),
        "b": ("INT", {"default": 0}),
    }},
    output_indices=(1,),
)
def bitwise_or(self, a, b):
    return (int(a) | int(b),)


@op(
    op_id="bitwise_xor",
    display_name="Bitwise XOR",
    category="Logic & Bits",
    input_schema={"required": {
        "a": ("INT", {"default": 0}),
        "b": ("INT", {"default": 0}),
    }},
    output_indices=(1,),
)
def bitwise_xor(self, a, b):
    return (int(a) ^ int(b),)


@op(
    op_id="bitwise_shift",
    display_name="Bitwise Shift",
    category="Logic & Bits",
    input_schema={"required": {
        "a": ("INT", {"default": 0}),
        "places": ("INT", {"default": 0, "min": -64, "max": 64}),
    }},
    output_indices=(1,),
    description="Positive places shifts left, negative shifts right.",
)
def bitwise_shift(self, a, places=0):
    if places >= 0:
        return (int(a) << places,)
    return (int(a) >> -places,)
