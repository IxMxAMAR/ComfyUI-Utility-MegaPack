"""Value / color operations on image tensors."""

import torch
from PIL import Image, ImageOps

from mp_shared.conversions import pil_to_tensor, tensor_to_pil

from .. import op


def _split_alpha(image):
    """Return (rgb, alpha) where alpha may be None.

    Operations on color should leave alpha untouched; this helper plus
    `_join_alpha` lets each op operate only on RGB and re-attach the original
    alpha channel for RGBA inputs.
    """
    if image.shape[-1] >= 4:
        return image[..., :3], image[..., 3:4]
    return image, None


def _join_alpha(rgb, alpha):
    if alpha is None:
        return rgb
    return torch.cat([rgb, alpha], dim=-1)


@op(
    op_id="invert",
    display_name="Invert",
    category="Value & Color",
    input_schema={"required": {"image": ("IMAGE", {})}},
    output_indices=(0,),
    description="Invert RGB values (1 - x). Alpha channel is preserved.",
)
def invert(self, image):
    rgb, alpha = _split_alpha(image)
    return (_join_alpha(1.0 - rgb, alpha),)


@op(
    op_id="color_shift_hsl",
    display_name="Color Shift (HSL)",
    category="Value & Color",
    input_schema={"required": {
        "image": ("IMAGE", {}),
        "hue_shift": ("FLOAT", {"default": 0.0, "min": -1.0, "max": 1.0}),
        "saturation": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 2.0}),
        "lightness": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 2.0}),
    }},
    output_indices=(0,),
    description="Shift hue (0..1 wraps the color wheel), scale saturation and lightness.",
)
def color_shift_hsl(self, image, hue_shift=0.0, saturation=1.0, lightness=1.0):
    pil = tensor_to_pil(image).convert("HSV")
    import numpy as np
    arr = np.asarray(pil).astype("float32")
    # H is 0..255 (PIL); shift then wrap.
    arr[..., 0] = (arr[..., 0] + hue_shift * 255.0) % 255.0
    arr[..., 1] = (arr[..., 1] * saturation).clip(0, 255)
    arr[..., 2] = (arr[..., 2] * lightness).clip(0, 255)
    out = Image.fromarray(arr.astype("uint8"), mode="HSV").convert("RGB")
    return (pil_to_tensor(out),)


@op(
    op_id="levels",
    display_name="Levels (black/white/gamma)",
    category="Value & Color",
    input_schema={"required": {
        "image": ("IMAGE", {}),
        "black_point": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 1.0}),
        "white_point": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0}),
        "gamma": ("FLOAT", {"default": 1.0, "min": 0.1, "max": 5.0}),
    }},
    output_indices=(0,),
    description="Remap the [black_point, white_point] range to [0, 1], then apply gamma.",
)
def levels(self, image, black_point=0.0, white_point=1.0, gamma=1.0):
    span = max(white_point - black_point, 1e-6)
    out = ((image - black_point) / span).clamp(0.0, 1.0)
    if gamma != 1.0:
        out = out.pow(1.0 / max(gamma, 1e-6))
    return (out,)


@op(
    op_id="posterize",
    display_name="Posterize",
    category="Value & Color",
    input_schema={"required": {
        "image": ("IMAGE", {}),
        "bits": ("INT", {"default": 4, "min": 1, "max": 8}),
    }},
    output_indices=(0,),
    description="Reduce per-channel bit depth.",
)
def posterize(self, image, bits=4):
    pil = ImageOps.posterize(tensor_to_pil(image), bits)
    return (pil_to_tensor(pil),)


@op(
    op_id="solarize",
    display_name="Solarize",
    category="Value & Color",
    input_schema={"required": {
        "image": ("IMAGE", {}),
        "threshold": ("FLOAT", {"default": 0.5, "min": 0.0, "max": 1.0}),
    }},
    output_indices=(0,),
    description="Invert all pixels above threshold.",
)
def solarize(self, image, threshold=0.5):
    pil = ImageOps.solarize(tensor_to_pil(image), int(threshold * 255))
    return (pil_to_tensor(pil),)


@op(
    op_id="threshold_binary",
    display_name="Threshold (binary)",
    category="Value & Color",
    input_schema={"required": {
        "image": ("IMAGE", {}),
        "threshold": ("FLOAT", {"default": 0.5, "min": 0.0, "max": 1.0}),
    }},
    output_indices=(0,),
    description="Pixels >= threshold become 1.0; the rest 0.0. Operates on luminance.",
)
def threshold_binary(self, image, threshold=0.5):
    luma = 0.299 * image[..., 0] + 0.587 * image[..., 1] + 0.114 * image[..., 2]
    mask = (luma >= threshold).float().unsqueeze(-1)
    # Broadcast across the 3 color channels; preserve the original alpha
    # channel if present. expand() returns a non-contiguous view, so
    # `.repeat` to materialize before re-attaching alpha.
    rgb = mask.repeat(1, 1, 1, 3) if image.dim() == 4 else mask.repeat(1, 1, 3)
    _, alpha = _split_alpha(image)
    return (_join_alpha(rgb, alpha),)


@op(
    op_id="color_match_histogram",
    display_name="Color Match (histogram transfer)",
    category="Value & Color",
    input_schema={"required": {
        "source": ("IMAGE", {}),
        "reference": ("IMAGE", {}),
        "strength": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0}),
    }},
    output_indices=(0,),
    description=(
        "Match `source`'s color distribution to `reference` using per-channel "
        "histogram CDF mapping. Use for compositing: blend a foreground render "
        "into a background plate without manual color-grading. `strength` "
        "linearly blends between the original source and the matched result."
    ),
)
def color_match_histogram(self, source, reference, strength=1.0):
    import numpy as np
    src = tensor_to_pil(source).convert("RGB")
    ref = tensor_to_pil(reference).convert("RGB")
    src_arr = np.asarray(src)
    ref_arr = np.asarray(ref)
    matched = np.empty_like(src_arr)
    for ch in range(3):
        # Build CDFs.
        s_vals, s_counts = np.unique(src_arr[..., ch].ravel(), return_counts=True)
        r_vals, r_counts = np.unique(ref_arr[..., ch].ravel(), return_counts=True)
        s_cdf = np.cumsum(s_counts).astype("float64")
        s_cdf /= s_cdf[-1]
        r_cdf = np.cumsum(r_counts).astype("float64")
        r_cdf /= r_cdf[-1]
        # For each source value, find the reference value with the closest CDF.
        interp = np.interp(s_cdf, r_cdf, r_vals).astype("uint8")
        lookup = np.zeros(256, dtype="uint8")
        lookup[s_vals] = interp
        matched[..., ch] = lookup[src_arr[..., ch]]
    matched_t = pil_to_tensor(Image.fromarray(matched))
    if strength >= 1.0:
        return (matched_t,)
    blended = source[..., :3] * (1.0 - strength) + matched_t[..., :3] * strength
    if source.shape[-1] >= 4:
        alpha = source[..., 3:4]
        blended = torch.cat([blended, alpha], dim=-1)
    return (blended.clamp(0.0, 1.0),)


@op(
    op_id="image_composite_over",
    display_name="Image Composite Over (alpha)",
    category="Value & Color",
    input_schema={"required": {
        "background": ("IMAGE", {}),
        "foreground": ("IMAGE", {}),
        "blend_mode": (["normal", "add", "multiply", "screen"], {"default": "normal"}),
        "opacity": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0}),
    }, "optional": {
        "mask": ("MASK", {}),
    }},
    output_indices=(0,),
    description=(
        "Composite `foreground` over `background`. If foreground is RGBA, its "
        "alpha is used; an optional MASK input also gates the composite. "
        "Blend modes: normal (alpha-over), add, multiply, screen."
    ),
)
def image_composite_over(self, background, foreground, blend_mode="normal", opacity=1.0, mask=None):
    bg = background[..., :3]
    if bg.shape[:-1] != foreground.shape[:-1]:
        # Resize foreground to match background using bilinear.
        import torch.nn.functional as F
        fg = foreground.permute(0, 3, 1, 2)
        fg = F.interpolate(fg, size=(bg.shape[-3], bg.shape[-2]), mode="bilinear", align_corners=False)
        foreground = fg.permute(0, 2, 3, 1)
    fg_rgb = foreground[..., :3]
    # Composite alpha: prefer explicit mask, fall back to foreground alpha.
    if mask is not None:
        if mask.dim() == 3:
            alpha_t = mask.unsqueeze(-1)
        elif mask.dim() == 4 and mask.shape[-1] == 1:
            alpha_t = mask
        else:
            alpha_t = mask.unsqueeze(0).unsqueeze(-1) if mask.dim() == 2 else mask
    elif foreground.shape[-1] >= 4:
        alpha_t = foreground[..., 3:4]
    else:
        alpha_t = torch.ones(*foreground.shape[:-1], 1, dtype=foreground.dtype, device=foreground.device)
    alpha_t = (alpha_t * opacity).clamp(0.0, 1.0)

    if blend_mode == "add":
        blended = (bg + fg_rgb).clamp(0.0, 1.0)
    elif blend_mode == "multiply":
        blended = (bg * fg_rgb).clamp(0.0, 1.0)
    elif blend_mode == "screen":
        blended = (1.0 - (1.0 - bg) * (1.0 - fg_rgb)).clamp(0.0, 1.0)
    else:  # normal
        blended = fg_rgb
    out = bg * (1.0 - alpha_t) + blended * alpha_t
    # Preserve original background alpha if RGBA.
    if background.shape[-1] >= 4:
        out = torch.cat([out, background[..., 3:4]], dim=-1)
    return (out.clamp(0.0, 1.0),)
