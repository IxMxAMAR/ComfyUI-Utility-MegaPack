"""Style operations: noise, film grain, JPEG quality degrade, glitch, halftone."""

import io
import random as _random

import torch
from PIL import Image

from mp_shared.conversions import pil_to_tensor, tensor_to_pil

from .. import op


@op(
    op_id="noise_add",
    display_name="Noise Add (Gaussian)",
    category="Style",
    input_schema={"required": {
        "image": ("IMAGE", {}),
        "amount": ("FLOAT", {"default": 0.05, "min": 0.0, "max": 1.0}),
        "seed": ("INT", {"default": -1, "min": -1, "max": 0xFFFFFFFF}),
    }},
    output_indices=(0,),
)
def noise_add(self, image, amount=0.05, seed=-1):
    g = torch.Generator(device=image.device)
    if seed >= 0:
        g.manual_seed(seed)
    noise = torch.randn(image.shape, generator=g, device=image.device) * amount
    return ((image + noise).clamp(0.0, 1.0),)


@op(
    op_id="film_grain",
    display_name="Film Grain",
    category="Style",
    input_schema={"required": {
        "image": ("IMAGE", {}),
        "amount": ("FLOAT", {"default": 0.08, "min": 0.0, "max": 0.5}),
        "luminance_dependence": ("FLOAT", {"default": 0.5, "min": 0.0, "max": 1.0}),
        "seed": ("INT", {"default": -1, "min": -1, "max": 0xFFFFFFFF}),
    }},
    output_indices=(0,),
    description="Adds grain that's stronger in midtones (controlled by luminance_dependence).",
)
def film_grain(self, image, amount=0.08, luminance_dependence=0.5, seed=-1):
    g = torch.Generator(device=image.device)
    if seed >= 0:
        g.manual_seed(seed)
    noise = torch.randn(image.shape, generator=g, device=image.device) * amount
    luma = 0.299 * image[..., 0:1] + 0.587 * image[..., 1:2] + 0.114 * image[..., 2:3]
    midtone_factor = 1.0 - (2.0 * (luma - 0.5).abs())
    factor = (1.0 - luminance_dependence) + luminance_dependence * midtone_factor
    return ((image + noise * factor).clamp(0.0, 1.0),)


@op(
    op_id="quality_degrade_jpeg",
    display_name="Quality Degrade (JPEG round-trip)",
    category="Style",
    input_schema={"required": {
        "image": ("IMAGE", {}),
        "quality": ("INT", {"default": 30, "min": 1, "max": 100}),
    }},
    output_indices=(0,),
    description="Re-encode each frame as JPEG at the chosen quality, then decode back. Simulates compression artifacts.",
)
def quality_degrade_jpeg(self, image, quality=30):
    out_frames = []
    for i in range(image.shape[0]):
        pil = tensor_to_pil(image, frame=i).convert("RGB")
        buf = io.BytesIO()
        pil.save(buf, format="JPEG", quality=int(quality))
        buf.seek(0)
        decoded = Image.open(buf).convert("RGB")
        out_frames.append(pil_to_tensor(decoded))
    return (torch.cat(out_frames, dim=0),)


@op(
    op_id="glitch_shift",
    display_name="Glitch (horizontal strip shift)",
    category="Style",
    input_schema={"required": {
        "image": ("IMAGE", {}),
        "strips": ("INT", {"default": 8, "min": 1, "max": 64}),
        "max_shift": ("INT", {"default": 16, "min": 0, "max": 256}),
        "seed": ("INT", {"default": -1, "min": -1, "max": 0xFFFFFFFF}),
    }},
    output_indices=(0,),
    description="Slice the image into horizontal strips and shift each by a random offset.",
)
def glitch_shift(self, image, strips=8, max_shift=16, seed=-1):
    rng = _random.Random() if seed == -1 else _random.Random(seed)
    h = image.shape[1]
    strip_h = max(1, h // strips)
    out = image.clone()
    for s in range(strips):
        y0 = s * strip_h
        y1 = h if s == strips - 1 else y0 + strip_h
        shift = rng.randint(-max_shift, max_shift)
        out[:, y0:y1, :, :] = torch.roll(image[:, y0:y1, :, :], shifts=shift, dims=2)
    return (out,)


@op(
    op_id="halftone_dots",
    display_name="Halftone (simple dot pattern)",
    category="Style",
    input_schema={"required": {
        "image": ("IMAGE", {}),
        "dot_size": ("INT", {"default": 6, "min": 2, "max": 32}),
    }},
    output_indices=(0,),
    description="Quick halftone approximation: per-cell luminance maps to a dot radius.",
)
def halftone_dots(self, image, dot_size=6):
    # v0.2.x allocated a full-image `np.ogrid[:h, :w]` *inside* the per-cell
    # loop. On a 1024² image with dot_size=6 that was ~30B ops and the worker
    # would freeze for many seconds. Now operates on cell-local coords:
    # ~30k cells × 36 ops each = ~1M ops, which is fast.
    import numpy as np
    pil = tensor_to_pil(image).convert("L")
    arr = np.asarray(pil)
    h, w = arr.shape
    out = np.full_like(arr, 255)
    half = dot_size / 2
    for y in range(0, h, dot_size):
        for x in range(0, w, dot_size):
            cell = arr[y:y + dot_size, x:x + dot_size]
            if cell.size == 0:
                continue
            v = cell.mean() / 255.0
            radius = int((1.0 - v) * half)
            if radius <= 0:
                continue
            ch, cw = cell.shape
            cy = ch / 2
            cx = cw / 2
            yy, xx = np.ogrid[:ch, :cw]
            mask = ((yy - cy) ** 2 + (xx - cx) ** 2) <= radius ** 2
            # Slice-assign into the local cell view.
            out[y:y + ch, x:x + cw][mask] = 0
    rgb = np.stack([out, out, out], axis=-1).astype("uint8")
    return (pil_to_tensor(Image.fromarray(rgb)),)


@op(
    op_id="frequency_separation",
    display_name="Frequency Separation (low/high split)",
    category="Style",
    input_schema={"required": {
        "image": ("IMAGE", {}),
        "blur_radius": ("INT", {"default": 8, "min": 1, "max": 64}),
        "output_kind": (["high_frequency", "low_frequency"], {"default": "high_frequency"}),
    }},
    output_indices=(0,),
    description=(
        "Pro retouching primitive. Splits an image into low-freq (color/tone) "
        "and high-freq (detail/texture) components by subtracting a Gaussian "
        "blur from the original. Run twice — once with `low_frequency`, once "
        "with `high_frequency` — to get both layers, edit independently, "
        "recombine with `image_composite_over` in add mode."
    ),
)
def frequency_separation(self, image, blur_radius=8, output_kind="high_frequency"):
    from PIL import ImageFilter
    pil = tensor_to_pil(image)
    blurred = pil.filter(ImageFilter.GaussianBlur(radius=int(blur_radius)))
    low = pil_to_tensor(blurred)
    if output_kind == "low_frequency":
        return (low,)
    # High-frequency = original - low + 0.5 (mid-gray pivot, standard convention).
    high = (image[..., :3] - low[..., :3] + 0.5).clamp(0.0, 1.0)
    if image.shape[-1] >= 4:
        alpha = image[..., 3:4]
        high = torch.cat([high, alpha], dim=-1)
    return (high,)
