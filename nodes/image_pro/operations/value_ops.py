"""Value / color operations on image tensors."""

from PIL import Image, ImageOps

from shared.conversions import pil_to_tensor, tensor_to_pil

from .. import op


@op(
    op_id="invert",
    display_name="Invert",
    category="Value & Color",
    input_schema={"required": {"image": ("IMAGE", {})}},
    output_indices=(0,),
    description="Invert RGB values (1 - x).",
)
def invert(self, image):
    return (1.0 - image,)


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
    mask = (luma >= threshold).float()
    out = mask.unsqueeze(-1).expand_as(image)
    return (out,)
