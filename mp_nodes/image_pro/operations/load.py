"""Image loaders: path, glob, random-from-folder, last-saved."""

import glob as _glob
import json
import os
import random

from PIL import Image, ExifTags

from mp_shared.conversions import pil_to_tensor

from .. import op


def _load_pil_with_metadata(path: str) -> tuple:
    img = Image.open(path)
    img.load()
    width, height = img.size
    exif = {}
    try:
        raw = img.getexif()
        if raw:
            for k, v in raw.items():
                tag = ExifTags.TAGS.get(k, str(k))
                if isinstance(v, (str, int, float)):
                    exif[tag] = v
    except Exception:
        pass
    metadata = json.dumps({"path": path, "format": img.format, "mode": img.mode, "exif": exif})
    return img, width, height, metadata


@op(
    op_id="load_image_path",
    display_name="Load Image (path)",
    category="Loaders",
    input_schema={"required": {"path": ("STRING", {"default": ""})}},
    output_indices=(0, 2, 3, 4),
    description="Load image by absolute or relative path. Outputs: image, width, height, metadata_json.",
)
def load_image_path(self, path):
    if not path or not os.path.isfile(path):
        raise FileNotFoundError(f"image not found: {path!r}")
    img, w, h, meta = _load_pil_with_metadata(path)
    return (pil_to_tensor(img.convert("RGB")), w, h, meta)


@op(
    op_id="load_image_glob",
    display_name="Load Image (glob, last)",
    category="Loaders",
    input_schema={"required": {
        "pattern": ("STRING", {"default": "*.png"}),
    }},
    output_indices=(0, 2, 3, 4),
    description="Load the most recent file matching a glob pattern.",
)
def load_image_glob(self, pattern):
    matches = sorted(_glob.glob(pattern), key=os.path.getmtime, reverse=True)
    if not matches:
        raise FileNotFoundError(f"no files match pattern: {pattern!r}")
    img, w, h, meta = _load_pil_with_metadata(matches[0])
    return (pil_to_tensor(img.convert("RGB")), w, h, meta)


@op(
    op_id="load_image_random_from_folder",
    display_name="Load Image (random from folder)",
    category="Loaders",
    input_schema={"required": {
        "folder": ("STRING", {"default": ""}),
        "seed": ("INT", {"default": -1, "min": -1, "max": 0xFFFFFFFF}),
    }},
    output_indices=(0, 2, 3, 4),
    description="Pick a random image from the folder. seed = -1 means non-deterministic.",
)
def load_image_random_from_folder(self, folder, seed=-1):
    if not folder or not os.path.isdir(folder):
        raise NotADirectoryError(f"folder not found: {folder!r}")
    candidates = [
        os.path.join(folder, f) for f in os.listdir(folder)
        if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".bmp"))
    ]
    if not candidates:
        raise FileNotFoundError(f"no images in folder: {folder!r}")
    rng = random.Random() if seed == -1 else random.Random(seed)
    chosen = rng.choice(candidates)
    img, w, h, meta = _load_pil_with_metadata(chosen)
    return (pil_to_tensor(img.convert("RGB")), w, h, meta)


@op(
    op_id="load_image_last_saved",
    display_name="Load Image (last saved in folder)",
    category="Loaders",
    input_schema={"required": {"folder": ("STRING", {"default": ""})}},
    output_indices=(0, 2, 3, 4),
    description="Load the most recently modified image in the folder.",
)
def load_image_last_saved(self, folder):
    if not folder or not os.path.isdir(folder):
        raise NotADirectoryError(f"folder not found: {folder!r}")
    candidates = [
        os.path.join(folder, f) for f in os.listdir(folder)
        if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".bmp"))
    ]
    if not candidates:
        raise FileNotFoundError(f"no images in folder: {folder!r}")
    chosen = max(candidates, key=os.path.getmtime)
    img, w, h, meta = _load_pil_with_metadata(chosen)
    return (pil_to_tensor(img.convert("RGB")), w, h, meta)


@op(
    op_id="load_image_sequence_nth",
    display_name="Load Image (Nth in sequence)",
    category="Loaders",
    input_schema={"required": {
        "folder": ("STRING", {"default": ""}),
        "index": ("INT", {"default": 0, "min": 0, "max": 100000}),
    }},
    output_indices=(0, 2, 3, 4),
    description="Load the Nth alphabetically-sorted image in the folder. Modulo wrap-around.",
)
def load_image_sequence_nth(self, folder, index=0):
    if not folder or not os.path.isdir(folder):
        raise NotADirectoryError(f"folder not found: {folder!r}")
    candidates = sorted(
        os.path.join(folder, f) for f in os.listdir(folder)
        if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".bmp"))
    )
    if not candidates:
        raise FileNotFoundError(f"no images in folder: {folder!r}")
    chosen = candidates[index % len(candidates)]
    img, w, h, meta = _load_pil_with_metadata(chosen)
    return (pil_to_tensor(img.convert("RGB")), w, h, meta)
