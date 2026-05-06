"""Latent operations: inspect, math, noise inject, smart upscale."""

import torch
import torch.nn.functional as F

from .. import op


def _samples_of(latent) -> torch.Tensor:
    """ComfyUI latents are dicts with a 'samples' tensor of shape (B, C, H, W)."""
    if isinstance(latent, dict) and "samples" in latent:
        return latent["samples"]
    raise ValueError("latent must be a dict with key 'samples' (a tensor)")


@op(
    op_id="latent_inspect",
    display_name="Latent Inspect",
    category="Latent",
    input_schema={"required": {"latent": ("LATENT", {})}},
    output_indices=(2,),
    description="Returns DICT with shape, dtype, and value range.",
)
def latent_inspect(self, latent):
    s = _samples_of(latent)
    return ({
        "shape": list(s.shape),
        "dtype": str(s.dtype),
        "min": round(float(s.min().item()), 6),
        "max": round(float(s.max().item()), 6),
        "mean": round(float(s.mean().item()), 6),
    },)


@op(
    op_id="latent_math",
    display_name="Latent Math (add/sub/blend)",
    category="Latent",
    input_schema={"required": {
        "a": ("LATENT", {}),
        "b": ("LATENT", {}),
        "math_op": (["add", "subtract", "blend"], {"default": "blend"}),
        "weight": ("FLOAT", {"default": 0.5, "min": 0.0, "max": 1.0}),
    }},
    output_indices=(1,),
    description="add: a+b. subtract: a-b. blend: lerp(a, b, weight).",
)
def latent_math(self, a, b, math_op="blend", weight=0.5):
    sa, sb = _samples_of(a), _samples_of(b)
    if sa.shape != sb.shape:
        raise ValueError(f"latent shape mismatch: {tuple(sa.shape)} vs {tuple(sb.shape)}")
    if math_op == "add":
        out = sa + sb
    elif math_op == "subtract":
        out = sa - sb
    elif math_op == "blend":
        out = sa * (1.0 - weight) + sb * weight
    else:
        raise ValueError(f"unknown math_op: {math_op}")
    return ({"samples": out},)


@op(
    op_id="latent_noise_inject",
    display_name="Latent Noise Inject",
    category="Latent",
    input_schema={"required": {
        "latent": ("LATENT", {}),
        "strength": ("FLOAT", {"default": 0.1, "min": 0.0, "max": 2.0}),
        "seed": ("INT", {"default": -1, "min": -1, "max": 0xFFFFFFFF}),
    }},
    output_indices=(1,),
    description="Add gaussian noise scaled by `strength`.",
)
def latent_noise_inject(self, latent, strength=0.1, seed=-1):
    s = _samples_of(latent)
    g = torch.Generator(device=s.device)
    if seed >= 0:
        g.manual_seed(seed)
    noise = torch.randn(s.shape, generator=g, device=s.device, dtype=s.dtype)
    return ({"samples": s + noise * strength},)


@op(
    op_id="latent_upscale_smart",
    display_name="Latent Upscale (smart method)",
    category="Latent",
    input_schema={"required": {
        "latent": ("LATENT", {}),
        "scale": ("FLOAT", {"default": 1.5, "min": 0.25, "max": 8.0}),
    }},
    output_indices=(1,),
    description="Auto-picks bilinear for scale<=2.0, bicubic for >2.0.",
)
def latent_upscale_smart(self, latent, scale=1.5):
    s = _samples_of(latent)
    method = "bilinear" if scale <= 2.0 else "bicubic"
    new_h = max(1, int(round(s.shape[-2] * scale)))
    new_w = max(1, int(round(s.shape[-1] * scale)))
    out = F.interpolate(s, size=(new_h, new_w), mode=method, align_corners=False)
    return ({"samples": out},)
