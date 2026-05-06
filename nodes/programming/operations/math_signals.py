"""Math, statistics, and randomness."""

import random
import statistics

from .. import op


@op(
    op_id="math_add",
    display_name="Math Add",
    category="Math & Signals",
    input_schema={"required": {
        "a": ("FLOAT", {"default": 0.0}),
        "b": ("FLOAT", {"default": 0.0}),
    }},
    output_indices=(2,),
)
def math_add(self, a, b):
    return (float(a) + float(b),)


@op(
    op_id="math_subtract",
    display_name="Math Subtract",
    category="Math & Signals",
    input_schema={"required": {
        "a": ("FLOAT", {"default": 0.0}),
        "b": ("FLOAT", {"default": 0.0}),
    }},
    output_indices=(2,),
)
def math_subtract(self, a, b):
    return (float(a) - float(b),)


@op(
    op_id="math_multiply",
    display_name="Math Multiply",
    category="Math & Signals",
    input_schema={"required": {
        "a": ("FLOAT", {"default": 0.0}),
        "b": ("FLOAT", {"default": 0.0}),
    }},
    output_indices=(2,),
)
def math_multiply(self, a, b):
    return (float(a) * float(b),)


@op(
    op_id="math_divide",
    display_name="Math Divide",
    category="Math & Signals",
    input_schema={"required": {
        "a": ("FLOAT", {"default": 0.0}),
        "b": ("FLOAT", {"default": 1.0}),
    }},
    output_indices=(2,),
    description="Raises ZeroDivisionError when b == 0.",
)
def math_divide(self, a, b):
    if b == 0:
        raise ZeroDivisionError("division by zero")
    return (float(a) / float(b),)


@op(
    op_id="math_clamp",
    display_name="Math Clamp",
    category="Math & Signals",
    input_schema={"required": {
        "value": ("FLOAT", {"default": 0.0}),
        "lo": ("FLOAT", {"default": 0.0}),
        "hi": ("FLOAT", {"default": 1.0}),
    }},
    output_indices=(2,),
)
def math_clamp(self, value, lo, hi):
    return (float(max(lo, min(hi, value))),)


@op(
    op_id="math_lerp",
    display_name="Math Lerp",
    category="Math & Signals",
    input_schema={"required": {
        "a": ("FLOAT", {"default": 0.0}),
        "b": ("FLOAT", {"default": 1.0}),
        "t": ("FLOAT", {"default": 0.5, "min": 0.0, "max": 1.0}),
    }},
    output_indices=(2,),
)
def math_lerp(self, a, b, t):
    return (float(a) + (float(b) - float(a)) * float(t),)


@op(
    op_id="stats_mean",
    display_name="Stats Mean",
    category="Math & Signals",
    input_schema={"required": {"values": ("LIST", {"default": []})}},
    output_indices=(2,),
)
def stats_mean(self, values):
    if not values:
        return (0.0,)
    return (float(statistics.fmean(values)),)


@op(
    op_id="stats_median",
    display_name="Stats Median",
    category="Math & Signals",
    input_schema={"required": {"values": ("LIST", {"default": []})}},
    output_indices=(2,),
)
def stats_median(self, values):
    if not values:
        return (0.0,)
    return (float(statistics.median(values)),)


@op(
    op_id="stats_std",
    display_name="Stats Stdev (population)",
    category="Math & Signals",
    input_schema={"required": {"values": ("LIST", {"default": []})}},
    output_indices=(2,),
    description="Population standard deviation. Returns 0 for fewer than 2 values.",
)
def stats_std(self, values):
    if not values or len(values) < 2:
        return (0.0,)
    return (float(statistics.pstdev(values)),)


@op(
    op_id="random_uniform",
    display_name="Random Uniform",
    category="Math & Signals",
    input_schema={"required": {
        "lo": ("FLOAT", {"default": 0.0}),
        "hi": ("FLOAT", {"default": 1.0}),
        "seed": ("INT", {"default": -1, "min": -1, "max": 0xFFFFFFFF}),
    }},
    output_indices=(2,),
    description="seed = -1 means non-deterministic; otherwise reproducible.",
)
def random_uniform(self, lo, hi, seed=-1):
    rng = random.Random() if seed == -1 else random.Random(seed)
    return (rng.uniform(float(lo), float(hi)),)
