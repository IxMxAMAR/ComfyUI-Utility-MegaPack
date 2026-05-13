"""Mask operations: from-color, erode/dilate/blur, combine, inspect."""

import torch
import torch.nn.functional as F
from PIL import ImageFilter

from mp_shared.conversions import pil_to_tensor, tensor_to_pil

from .. import op


def _ensure_3d_mask(m: torch.Tensor) -> torch.Tensor:
    """Coerce mask to (B, H, W). Accepts (H, W), (B, H, W), or (B, H, W, 1)."""
    if m.dim() == 2:
        return m.unsqueeze(0)
    if m.dim() == 3:
        return m
    if m.dim() == 4 and m.shape[-1] == 1:
        return m.squeeze(-1)
    raise ValueError(f"unsupported mask shape: {tuple(m.shape)}")


@op(
    op_id="mask_from_color",
    display_name="Mask from Color",
    category="Mask",
    input_schema={"required": {
        "image": ("IMAGE", {}),
        "r": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0}),
        "g": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 1.0}),
        "b": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 1.0}),
        "tolerance": ("FLOAT", {"default": 0.05, "min": 0.0, "max": 1.0}),
    }},
    output_indices=(0,),
    description="Mask = 1 where pixel within `tolerance` of (r, g, b).",
)
def mask_from_color(self, image, r, g, b, tolerance=0.05):
    target = torch.tensor([r, g, b], device=image.device, dtype=image.dtype)
    diff = (image[..., :3] - target).abs().max(dim=-1).values
    mask = (diff <= tolerance).float()
    return (mask,)


@op(
    op_id="mask_erode",
    display_name="Mask Erode",
    category="Mask",
    input_schema={"required": {
        "mask": ("MASK", {}),
        "kernel_size": ("INT", {"default": 3, "min": 1, "max": 32}),
    }},
    output_indices=(0,),
    description="Min pooling erodes the mask (shrinks white regions).",
)
def mask_erode(self, mask, kernel_size=3):
    m = _ensure_3d_mask(mask).unsqueeze(1)
    pad = kernel_size // 2
    out = -F.max_pool2d(-m, kernel_size=kernel_size, stride=1, padding=pad)
    return (out.squeeze(1),)


@op(
    op_id="mask_dilate",
    display_name="Mask Dilate",
    category="Mask",
    input_schema={"required": {
        "mask": ("MASK", {}),
        "kernel_size": ("INT", {"default": 3, "min": 1, "max": 32}),
    }},
    output_indices=(0,),
    description="Max pooling dilates the mask (grows white regions).",
)
def mask_dilate(self, mask, kernel_size=3):
    m = _ensure_3d_mask(mask).unsqueeze(1)
    pad = kernel_size // 2
    out = F.max_pool2d(m, kernel_size=kernel_size, stride=1, padding=pad)
    return (out.squeeze(1),)


@op(
    op_id="mask_blur",
    display_name="Mask Blur (Gaussian)",
    category="Mask",
    input_schema={"required": {
        "mask": ("MASK", {}),
        "radius": ("FLOAT", {"default": 4.0, "min": 0.1, "max": 100.0}),
    }},
    output_indices=(0,),
)
def mask_blur(self, mask, radius=4.0):
    m = _ensure_3d_mask(mask)
    out_frames = []
    for i in range(m.shape[0]):
        # Lift to 3-channel image, run PIL gaussian, drop to 1 channel.
        m_3c = m[i].unsqueeze(-1).expand(-1, -1, 3)
        pil = tensor_to_pil(m_3c.unsqueeze(0)).filter(ImageFilter.GaussianBlur(radius=float(radius)))
        out_frames.append(pil_to_tensor(pil)[0, ..., 0])
    return (torch.stack(out_frames, dim=0),)


@op(
    op_id="mask_combine",
    display_name="Mask Combine (union/intersect/diff)",
    category="Mask",
    input_schema={"required": {
        "a": ("MASK", {}),
        "b": ("MASK", {}),
        "combine_op": (["union", "intersect", "diff", "xor"], {"default": "union"}),
    }},
    output_indices=(0,),
)
def mask_combine(self, a, b, combine_op="union"):
    a3 = _ensure_3d_mask(a)
    b3 = _ensure_3d_mask(b)
    if a3.shape != b3.shape:
        raise ValueError(f"mask shape mismatch: {tuple(a3.shape)} vs {tuple(b3.shape)}")
    if combine_op == "union":
        return (torch.maximum(a3, b3),)
    if combine_op == "intersect":
        return (torch.minimum(a3, b3),)
    if combine_op == "diff":
        return ((a3 - b3).clamp(0.0, 1.0),)
    if combine_op == "xor":
        return ((a3 + b3 - 2 * torch.minimum(a3, b3)).clamp(0.0, 1.0),)
    raise ValueError(f"unknown combine_op: {combine_op}")


@op(
    op_id="mask_inspect",
    display_name="Mask Inspect (coverage/bbox/centroid)",
    category="Mask",
    input_schema={"required": {"mask": ("MASK", {})}},
    output_indices=(2,),
    description="Returns DICT with coverage_pct, bbox [x0,y0,x1,y1], centroid [cx,cy].",
)
def mask_inspect(self, mask):
    m = _ensure_3d_mask(mask)[0]  # use first frame
    h, w = m.shape
    total = float(m.sum().item())
    coverage = total / float(h * w) if h * w else 0.0
    if total == 0:
        return ({"coverage_pct": 0.0, "bbox": [0, 0, 0, 0], "centroid": [0.0, 0.0]},)
    rows = (m.sum(dim=1) > 0).nonzero(as_tuple=True)[0]
    cols = (m.sum(dim=0) > 0).nonzero(as_tuple=True)[0]
    y0, y1 = int(rows.min().item()), int(rows.max().item())
    x0, x1 = int(cols.min().item()), int(cols.max().item())
    yy, xx = torch.meshgrid(torch.arange(h, dtype=m.dtype), torch.arange(w, dtype=m.dtype), indexing="ij")
    cx = float((xx * m).sum().item() / total)
    cy = float((yy * m).sum().item() / total)
    return ({
        "coverage_pct": round(coverage * 100, 4),
        "bbox": [x0, y0, x1, y1],
        "centroid": [round(cx, 2), round(cy, 2)],
    },)
