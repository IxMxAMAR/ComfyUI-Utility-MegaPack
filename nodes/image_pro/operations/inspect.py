"""Inspection ops: image info, palette extraction, channel ops, histogram, multi-image grid."""

import json

import torch

from shared.conversions import pil_to_tensor, tensor_to_pil

from .. import op


@op(
    op_id="image_info",
    display_name="Image Info",
    category="Inspect",
    input_schema={"required": {"image": ("IMAGE", {})}},
    output_indices=(2, 3, 4),
    description="Returns width, height, and a JSON metadata blob (channel count, batch size, mean RGB).",
)
def image_info(self, image):
    b, h, w, c = image.shape
    mean_rgb = image.mean(dim=(0, 1, 2)).tolist() if c >= 3 else [0.0, 0.0, 0.0]
    info = {
        "batch": int(b), "height": int(h), "width": int(w), "channels": int(c),
        "mean_rgb": [round(float(v), 4) for v in mean_rgb[:3]],
        "min": round(float(image.min().item()), 4),
        "max": round(float(image.max().item()), 4),
    }
    return (int(w), int(h), json.dumps(info))


@op(
    op_id="channel_op",
    display_name="Channel Op (swap/isolate)",
    category="Inspect",
    input_schema={"required": {
        "image": ("IMAGE", {}),
        "channel_action": (["swap_rgb_to_bgr", "isolate_r", "isolate_g", "isolate_b", "grayscale"], {"default": "grayscale"}),
    }},
    output_indices=(0,),
    description="`channel_action` is a separate widget name from `mode` (which is reserved for the op picker).",
)
def channel_op(self, image, channel_action="grayscale"):
    if channel_action == "swap_rgb_to_bgr":
        return (image[..., [2, 1, 0]] if image.shape[-1] >= 3 else image,)
    if channel_action == "isolate_r":
        out = torch.zeros_like(image); out[..., 0] = image[..., 0]; return (out,)
    if channel_action == "isolate_g":
        out = torch.zeros_like(image); out[..., 1] = image[..., 1]; return (out,)
    if channel_action == "isolate_b":
        out = torch.zeros_like(image); out[..., 2] = image[..., 2]; return (out,)
    # grayscale
    luma = 0.299 * image[..., 0] + 0.587 * image[..., 1] + 0.114 * image[..., 2]
    return (luma.unsqueeze(-1).expand_as(image),)


@op(
    op_id="palette_extract",
    display_name="Palette Extract (top-N colors)",
    category="Inspect",
    input_schema={"required": {
        "image": ("IMAGE", {}),
        "n_colors": ("INT", {"default": 5, "min": 2, "max": 32}),
    }},
    output_indices=(4,),
    description="Returns a JSON array of [r, g, b] tuples (0..255) using PIL's adaptive palette quantization.",
)
def palette_extract(self, image, n_colors=5):
    pil = tensor_to_pil(image).convert("RGB")
    quantized = pil.quantize(colors=int(n_colors), method=2)
    palette_bytes = quantized.getpalette()  # length 768
    used_indices = sorted({px for px in quantized.getdata()})[:n_colors]
    colors = []
    for idx in used_indices:
        r, g, b = palette_bytes[idx * 3], palette_bytes[idx * 3 + 1], palette_bytes[idx * 3 + 2]
        colors.append([int(r), int(g), int(b)])
    return (json.dumps(colors),)


@op(
    op_id="histogram_json",
    display_name="Histogram (JSON, 32 bins per channel)",
    category="Inspect",
    input_schema={"required": {"image": ("IMAGE", {})}},
    output_indices=(4,),
    description="32-bin histogram per RGB channel, as JSON {r:[...], g:[...], b:[...]}.",
)
def histogram_json(self, image):
    bins = 32
    hist = {}
    for i, name in enumerate(("r", "g", "b")):
        if image.shape[-1] <= i:
            hist[name] = [0] * bins
            continue
        h = torch.histc(image[..., i].float(), bins=bins, min=0.0, max=1.0)
        hist[name] = [int(v) for v in h.tolist()]
    return (json.dumps(hist),)
