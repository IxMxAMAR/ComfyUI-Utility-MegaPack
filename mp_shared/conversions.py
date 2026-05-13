"""Tensor ↔ PIL conversion helpers.

ComfyUI image tensors: shape (B, H, W, C), float32 in [0, 1], C=3 (RGB) or 4 (RGBA).
PIL images: H × W, mode "RGB" / "RGBA" / "L".
"""

from __future__ import annotations

import io

import numpy as np
import torch
from PIL import Image


def tensor_to_pil(tensor: torch.Tensor, frame: int = 0) -> Image.Image:
    """Convert a single frame from a ComfyUI image tensor to a PIL Image.

    Accepts shape (B, H, W, C) or (H, W, C). Returns PIL "RGB" or "RGBA".
    """
    if tensor.dim() == 4:
        arr = tensor[frame].detach().cpu().numpy()
    elif tensor.dim() == 3:
        arr = tensor.detach().cpu().numpy()
    else:
        raise ValueError(f"expected 3D or 4D tensor, got shape {tuple(tensor.shape)}")

    arr = np.clip(arr * 255.0, 0, 255).astype(np.uint8)
    if arr.shape[-1] == 4:
        return Image.fromarray(arr, mode="RGBA")
    if arr.shape[-1] == 3:
        return Image.fromarray(arr, mode="RGB")
    if arr.shape[-1] == 1:
        return Image.fromarray(arr.squeeze(-1), mode="L")
    raise ValueError(f"unsupported channel count: {arr.shape[-1]}")


def pil_to_tensor(image: Image.Image) -> torch.Tensor:
    """Convert a PIL Image to a ComfyUI image tensor of shape (1, H, W, C)."""
    if image.mode == "L":
        image = image.convert("RGB")
    arr = np.asarray(image).astype(np.float32) / 255.0
    if arr.ndim == 2:
        arr = arr[..., None]
    return torch.from_numpy(arr).unsqueeze(0)


def pil_to_bytes(image: Image.Image, fmt: str = "PNG", **kwargs) -> bytes:
    buf = io.BytesIO()
    image.save(buf, format=fmt, **kwargs)
    return buf.getvalue()


def bytes_to_pil(data: bytes) -> Image.Image:
    return Image.open(io.BytesIO(data))
