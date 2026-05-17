"""Resolution and aspect-ratio helpers."""

import math

from .. import op


_RATIO_PRESETS = {
    "1:1 (square)": (1, 1),
    "4:3": (4, 3),
    "3:2": (3, 2),
    "16:9": (16, 9),
    "21:9": (21, 9),
    "9:16 (portrait)": (9, 16),
    "3:4 (portrait)": (3, 4),
    "2:3 (portrait)": (2, 3),
}


_SDXL_BUCKETS = [
    (1024, 1024),
    (1152, 896),
    (896, 1152),
    (1216, 832),
    (832, 1216),
    (1344, 768),
    (768, 1344),
    (1536, 640),
    (640, 1536),
]


@op(
    op_id="aspect_ratio_pick",
    display_name="Aspect Ratio Pick",
    category="Resolution",
    input_schema={"required": {
        "preset": (list(_RATIO_PRESETS.keys()), {"default": "16:9"}),
        "long_side": ("INT", {"default": 1024, "min": 64, "max": 8192}),
    }},
    output_indices=(5, 6, 8),
    description="Returns width (out:5) and height (out:6) for the chosen ratio scaled to long_side.",
)
def aspect_ratio_pick(self, preset, long_side=1024):
    rw, rh = _RATIO_PRESETS.get(preset, (1, 1))
    if rw >= rh:
        w = int(long_side)
        h = int(round(long_side * rh / rw))
    else:
        h = int(long_side)
        w = int(round(long_side * rw / rh))
    # Snap to multiples of 8 — SD UNet/VAE require this (typically /8 or /64).
    # Without snapping, long_side=1000 + 16:9 produced 1000×562 which crashed
    # the model.
    w = max(8, (w // 8) * 8)
    h = max(8, (h // 8) * 8)
    info = {"preset": preset, "ratio": [rw, rh], "width": w, "height": h, "snapped_to": 8}
    return (w, h, info)


@op(
    op_id="sdxl_bucket_pick",
    display_name="SDXL Bucket Pick (9 official sizes)",
    category="Resolution",
    input_schema={"required": {"index": ("INT", {"default": 0, "min": 0, "max": 8})}},
    output_indices=(5, 6, 8),
    description="Pick one of the 9 official SDXL training resolutions by index.",
)
def sdxl_bucket_pick(self, index=0):
    w, h = _SDXL_BUCKETS[int(index) % len(_SDXL_BUCKETS)]
    return (w, h, {"index": int(index), "width": w, "height": h})


@op(
    op_id="snap_to_multiple",
    display_name="Snap to Multiple",
    category="Resolution",
    input_schema={"required": {
        "value": ("INT", {"default": 1024}),
        "multiple": ("INT", {"default": 8, "min": 1, "max": 1024}),
    }},
    output_indices=(5,),
    description="Round `value` to the nearest multiple of `multiple`.",
)
def snap_to_multiple(self, value, multiple=8):
    m = max(1, int(multiple))
    return (int(round(int(value) / m) * m),)


@op(
    op_id="megapixel_calculator",
    display_name="Megapixel Calculator (target MP + ratio)",
    category="Resolution",
    input_schema={"required": {
        "target_megapixels": ("FLOAT", {"default": 1.0, "min": 0.01, "max": 64.0}),
        "ratio_w": ("INT", {"default": 16, "min": 1, "max": 999}),
        "ratio_h": ("INT", {"default": 9, "min": 1, "max": 999}),
        "snap_multiple": ("INT", {"default": 8, "min": 1, "max": 1024}),
    }},
    output_indices=(5, 6, 8),
    description="Find W,H such that W*H ≈ target_megapixels * 1e6 with given ratio, snapped to multiple.",
)
def megapixel_calculator(self, target_megapixels, ratio_w, ratio_h, snap_multiple=8):
    target_pixels = float(target_megapixels) * 1_000_000
    ratio_w, ratio_h = int(ratio_w), int(ratio_h)
    # W = sqrt(target * ratio_w / ratio_h); H = W * ratio_h / ratio_w
    w = math.sqrt(target_pixels * ratio_w / ratio_h)
    h = w * ratio_h / ratio_w
    m = max(1, int(snap_multiple))
    w_snapped = int(round(w / m) * m)
    h_snapped = int(round(h / m) * m)
    return (w_snapped, h_snapped, {
        "width": w_snapped, "height": h_snapped,
        "actual_megapixels": round((w_snapped * h_snapped) / 1_000_000, 4),
    })
