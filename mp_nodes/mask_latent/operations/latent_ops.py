"""Latent operations: inspect, math, noise inject, smart upscale."""

import torch
import torch.nn.functional as F

from .. import op


def _samples_of(latent) -> torch.Tensor:
    """ComfyUI latents are dicts with a 'samples' tensor of shape (B, C, H, W)."""
    if isinstance(latent, dict) and "samples" in latent:
        return latent["samples"]
    raise ValueError("latent must be a dict with key 'samples' (a tensor)")


def _with_samples(latent: dict, samples: torch.Tensor) -> dict:
    """Return a SHALLOW copy of `latent` with `samples` swapped.

    Preserves auxiliary keys like `noise_mask` (used for inpainting) and
    `batch_index` that downstream ComfyUI nodes depend on. Previously these
    ops returned `{"samples": out}` and silently dropped everything else.
    """
    out = dict(latent) if isinstance(latent, dict) else {}
    out["samples"] = samples
    return out


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
    return (_with_samples(a, out),)


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
    return (_with_samples(latent, s + noise * strength),)


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
    return (_with_samples(latent, out),)


@op(
    op_id="latent_nan_guard",
    display_name="Latent NaN Guard",
    category="Latent",
    input_schema={"required": {
        "latent": ("LATENT", {}),
        "on_nan": (["raise", "zero_out", "clamp"], {"default": "raise"}),
    }},
    output_indices=(1, 2),
    description=(
        "Inspect a latent for NaN/Inf (common with SDXL FP16). "
        "`raise` stops the workflow with a clear error before VAE decode wastes "
        "GPU on a guaranteed-black image. `zero_out` replaces NaN/Inf with 0. "
        "`clamp` bounds extreme values to ±100."
    ),
)
def latent_nan_guard(self, latent, on_nan="raise"):
    s = _samples_of(latent)
    nan_count = int(torch.isnan(s).sum().item())
    inf_count = int(torch.isinf(s).sum().item())
    info = {"nan_count": nan_count, "inf_count": inf_count, "shape": list(s.shape)}
    if nan_count == 0 and inf_count == 0:
        return (latent, info)
    if on_nan == "raise":
        raise RuntimeError(
            f"latent contains {nan_count} NaN + {inf_count} Inf values "
            f"(shape={list(s.shape)}). Decode would produce a black image. "
            f"Switch on_nan to 'zero_out' or 'clamp' to recover."
        )
    if on_nan == "zero_out":
        out = torch.nan_to_num(s, nan=0.0, posinf=0.0, neginf=0.0)
    else:  # clamp
        out = torch.nan_to_num(s, nan=0.0, posinf=100.0, neginf=-100.0).clamp(-100.0, 100.0)
    return (_with_samples(latent, out), info)


@op(
    op_id="latent_pad_crop",
    display_name="Latent Pad/Crop",
    category="Latent",
    input_schema={"required": {
        "latent": ("LATENT", {}),
        "target_h": ("INT", {"default": 64, "min": 1, "max": 4096}),
        "target_w": ("INT", {"default": 64, "min": 1, "max": 4096}),
        "fill_value": ("FLOAT", {"default": 0.0, "min": -10.0, "max": 10.0}),
    }},
    output_indices=(1,),
    description=(
        "Pad (with `fill_value`) or center-crop a latent to (target_h, target_w) "
        "WITHOUT decoding to pixel space. Use to align latents for compositing "
        "or to match an SDXL bucket. Saves the VAE roundtrip."
    ),
)
def latent_pad_crop(self, latent, target_h=64, target_w=64, fill_value=0.0):
    s = _samples_of(latent)
    B, C, H, W = s.shape
    out = torch.full((B, C, target_h, target_w), float(fill_value), dtype=s.dtype, device=s.device)

    src_top = max(0, (H - target_h) // 2)
    src_left = max(0, (W - target_w) // 2)
    dst_top = max(0, (target_h - H) // 2)
    dst_left = max(0, (target_w - W) // 2)
    copy_h = min(H, target_h)
    copy_w = min(W, target_w)

    out[:, :, dst_top:dst_top + copy_h, dst_left:dst_left + copy_w] = \
        s[:, :, src_top:src_top + copy_h, src_left:src_left + copy_w]
    return (_with_samples(latent, out),)
