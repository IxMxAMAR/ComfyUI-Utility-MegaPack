"""Spatial operations: pixelate, blur, sharpen, chromatic aberration, vignette."""

from PIL import Image, ImageFilter

from shared.conversions import pil_to_tensor, tensor_to_pil

from .. import op


@op(
    op_id="pixelate",
    display_name="Pixelate",
    category="Spatial",
    input_schema={"required": {
        "image": ("IMAGE", {}),
        "block_size": ("INT", {"default": 8, "min": 2, "max": 256}),
    }},
    output_indices=(0,),
)
def pixelate(self, image, block_size=8):
    pil = tensor_to_pil(image)
    w, h = pil.size
    small = pil.resize((max(1, w // block_size), max(1, h // block_size)), Image.NEAREST)
    out = small.resize((w, h), Image.NEAREST)
    return (pil_to_tensor(out),)


@op(
    op_id="blur_gaussian",
    display_name="Blur (Gaussian)",
    category="Spatial",
    input_schema={"required": {
        "image": ("IMAGE", {}),
        "radius": ("FLOAT", {"default": 2.0, "min": 0.1, "max": 100.0}),
    }},
    output_indices=(0,),
)
def blur_gaussian(self, image, radius=2.0):
    pil = tensor_to_pil(image).filter(ImageFilter.GaussianBlur(radius=float(radius)))
    return (pil_to_tensor(pil),)


@op(
    op_id="sharpen_unsharp",
    display_name="Sharpen (Unsharp Mask)",
    category="Spatial",
    input_schema={"required": {
        "image": ("IMAGE", {}),
        "radius": ("FLOAT", {"default": 2.0, "min": 0.1, "max": 50.0}),
        "amount": ("INT", {"default": 150, "min": 0, "max": 500}),
        "threshold": ("INT", {"default": 3, "min": 0, "max": 255}),
    }},
    output_indices=(0,),
)
def sharpen_unsharp(self, image, radius=2.0, amount=150, threshold=3):
    pil = tensor_to_pil(image).filter(
        ImageFilter.UnsharpMask(radius=float(radius), percent=int(amount), threshold=int(threshold))
    )
    return (pil_to_tensor(pil),)


@op(
    op_id="chromatic_aberration",
    display_name="Chromatic Aberration",
    category="Spatial",
    input_schema={"required": {
        "image": ("IMAGE", {}),
        "shift_pixels": ("INT", {"default": 4, "min": 0, "max": 64}),
    }},
    output_indices=(0,),
    description="Shift R left and B right by N pixels.",
)
def chromatic_aberration(self, image, shift_pixels=4):
    import torch
    if shift_pixels == 0:
        return (image,)
    out = image.clone()
    # image shape (B, H, W, C)
    out[..., 0] = torch.roll(image[..., 0], shifts=-shift_pixels, dims=-1)
    out[..., 2] = torch.roll(image[..., 2], shifts=shift_pixels, dims=-1)
    return (out,)


@op(
    op_id="vignette",
    display_name="Vignette",
    category="Spatial",
    input_schema={"required": {
        "image": ("IMAGE", {}),
        "strength": ("FLOAT", {"default": 0.5, "min": 0.0, "max": 1.0}),
        "softness": ("FLOAT", {"default": 0.6, "min": 0.1, "max": 1.0}),
    }},
    output_indices=(0,),
    description="Darken the corners with a radial falloff.",
)
def vignette(self, image, strength=0.5, softness=0.6):
    import torch
    h, w = image.shape[1], image.shape[2]
    yy, xx = torch.meshgrid(
        torch.linspace(-1, 1, h, device=image.device),
        torch.linspace(-1, 1, w, device=image.device),
        indexing="ij",
    )
    radius = (xx ** 2 + yy ** 2).sqrt()
    falloff = (1.0 - (radius / max(softness, 1e-3)).clamp(0.0, 1.0)) ** 2
    mask = (1.0 - strength) + strength * falloff
    return ((image * mask.unsqueeze(0).unsqueeze(-1)).clamp(0.0, 1.0),)


@op(
    op_id="lens_distortion",
    display_name="Lens Distortion (barrel/pincushion)",
    category="Spatial",
    input_schema={"required": {
        "image": ("IMAGE", {}),
        "k": ("FLOAT", {"default": 0.2, "min": -1.0, "max": 1.0}),
    }},
    output_indices=(0,),
    description="Positive k = barrel (bulge); negative = pincushion. Quick and dirty radial warp.",
)
def lens_distortion(self, image, k=0.2):
    import torch
    import torch.nn.functional as F
    b, h, w, c = image.shape
    # Build flow grid in normalized coords (-1, 1)
    yy, xx = torch.meshgrid(
        torch.linspace(-1, 1, h, device=image.device),
        torch.linspace(-1, 1, w, device=image.device),
        indexing="ij",
    )
    r2 = xx ** 2 + yy ** 2
    factor = 1.0 + k * r2
    grid_x = xx * factor
    grid_y = yy * factor
    grid = torch.stack([grid_x, grid_y], dim=-1).unsqueeze(0).expand(b, -1, -1, -1)
    # F.grid_sample expects (B, C, H, W); convert
    img_chw = image.permute(0, 3, 1, 2)
    out_chw = F.grid_sample(img_chw, grid, mode="bilinear", padding_mode="zeros", align_corners=True)
    out = out_chw.permute(0, 2, 3, 1).contiguous()
    return (out.clamp(0.0, 1.0),)


@op(
    op_id="tile_repeat",
    display_name="Tile Repeat",
    category="Spatial",
    input_schema={"required": {
        "image": ("IMAGE", {}),
        "cols": ("INT", {"default": 2, "min": 1, "max": 16}),
        "rows": ("INT", {"default": 2, "min": 1, "max": 16}),
    }},
    output_indices=(0,),
)
def tile_repeat(self, image, cols=2, rows=2):
    import torch
    return (image.repeat(1, rows, cols, 1),)
