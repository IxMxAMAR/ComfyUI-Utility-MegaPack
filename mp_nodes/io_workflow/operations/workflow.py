"""Workflow ops: save-with-manifest, filename builder, notify, stop, assert, sweep, watch."""

import datetime as _dt
import io
import json as _json
import os
import re
import sys
import time

import torch
from PIL import Image

import requests

from mp_shared.conversions import tensor_to_pil

from .. import op


_SLUG_RE = re.compile(r"[^a-z0-9]+")


def _slug(text: str, max_length: int = 30) -> str:
    s = _SLUG_RE.sub("-", text.lower()).strip("-")
    return s[:max_length].rstrip("-") or "untitled"


@op(
    op_id="filename_format",
    display_name="Filename Format",
    category="Workflow",
    input_schema={"required": {
        "template": ("STRING", {"default": "{date}_{seed}_{prompt_slug}.png"}),
        "seed": ("INT", {"default": 0}),
        "prompt": ("STRING", {"default": ""}),
        "extension": ("STRING", {"default": "png"}),
    }},
    output_indices=(0,),
    description="Tokens: {date}, {time}, {datetime}, {seed}, {prompt_slug}, {ext}.",
)
def filename_format(self, template, seed=0, prompt="", extension="png"):
    now = _dt.datetime.now()
    tokens = {
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H-%M-%S"),
        "datetime": now.strftime("%Y-%m-%d_%H-%M-%S"),
        "seed": str(int(seed)),
        "prompt_slug": _slug(prompt),
        "ext": extension.lstrip("."),
    }
    out = template
    for k, v in tokens.items():
        out = out.replace("{" + k + "}", v)
    return (out,)


@op(
    op_id="save_image_with_manifest",
    display_name="Save Image with Manifest",
    category="Workflow",
    input_schema={"required": {
        "image": ("IMAGE", {}),
        "output_dir": ("STRING", {"default": ""}),
        "filename": ("STRING", {"default": "output.png"}),
        "manifest_json": ("STRING", {"default": "{}", "multiline": True}),
    }},
    output_indices=(0,),
    description="Save image + .json sidecar containing the manifest. Returns the saved image path.",
)
def save_image_with_manifest(self, image, output_dir, filename, manifest_json="{}"):
    if not output_dir:
        raise ValueError("output_dir is required")
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, filename)
    pil = tensor_to_pil(image)
    pil.save(path)
    sidecar = os.path.splitext(path)[0] + ".json"
    parsed = _json.loads(manifest_json) if manifest_json else {}
    with open(sidecar, "w", encoding="utf-8") as f:
        _json.dump({**parsed, "image": filename, "saved_at": _dt.datetime.now().isoformat()}, f, indent=2)
    return (path,)


@op(
    op_id="notify_webhook",
    display_name="Notify (webhook)",
    category="Workflow",
    input_schema={"required": {
        "url": ("STRING", {"default": ""}),
        "message": ("STRING", {"default": "", "multiline": True}),
        "timeout_seconds": ("INT", {"default": 10, "min": 1, "max": 60}),
    }},
    output_indices=(3,),
    description="POST {message} to the webhook. Returns HTTP status code.",
)
def notify_webhook(self, url, message, timeout_seconds=10):
    if not url:
        raise ValueError("url is required")
    resp = requests.post(url, json={"message": message}, timeout=int(timeout_seconds))
    return (int(resp.status_code),)


@op(
    op_id="notify_console",
    display_name="Notify (console)",
    category="Workflow",
    input_schema={"required": {
        "label": ("STRING", {"default": "MegaPack"}),
        "message": ("STRING", {"default": "", "multiline": True}),
    }},
    output_indices=(0,),
    description="Print labeled message to stderr.",
)
def notify_console(self, label, message):
    line = f"[{label}] {message}"
    print(line, file=sys.stderr, flush=True)
    return (line,)


@op(
    op_id="workflow_stop",
    display_name="Workflow Stop",
    category="Workflow",
    input_schema={"required": {
        "condition": ("BOOLEAN", {"default": False}),
        "message": ("STRING", {"default": "stopped by Utility-MegaPack"}),
    }},
    output_indices=(0,),
    description="If condition is true, raise to abort the workflow.",
)
def workflow_stop(self, condition, message="stopped by Utility-MegaPack"):
    if condition:
        raise RuntimeError(message)
    return ("",)


@op(
    op_id="workflow_assert",
    display_name="Workflow Assert",
    category="Workflow",
    input_schema={"required": {
        "condition": ("BOOLEAN", {"default": True}),
        "message": ("STRING", {"default": "assertion failed"}),
    }},
    output_indices=(0,),
    description="Raise if condition is False.",
)
def workflow_assert(self, condition, message="assertion failed"):
    if not condition:
        raise AssertionError(message)
    return ("ok",)


@op(
    op_id="sweep_param",
    display_name="Sweep Parameter (range)",
    category="Workflow",
    input_schema={"required": {
        "start": ("FLOAT", {"default": 0.0}),
        "stop": ("FLOAT", {"default": 1.0}),
        "step": ("FLOAT", {"default": 0.1, "min": 0.0001, "max": 1000.0}),
    }},
    output_indices=(1,),
    description="Returns DICT with `values` list — useful for X/Y plot composition.",
)
def sweep_param(self, start, stop, step=0.1):
    if step <= 0:
        raise ValueError("step must be > 0")
    out = []
    v = float(start)
    while v < float(stop) + 1e-12:
        out.append(round(v, 6))
        v += float(step)
    return ({"values": out, "count": len(out)},)


@op(
    op_id="watch_folder_next",
    display_name="Watch Folder (next file)",
    category="Workflow",
    input_schema={"required": {
        "folder": ("STRING", {"default": ""}),
        "wait_seconds": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 60.0}),
        "extensions": ("STRING", {"default": ".png,.jpg,.jpeg,.webp"}),
    }},
    output_indices=(0,),
    description="Return the most-recent file matching extensions. wait_seconds polls until something appears.",
)
def watch_folder_next(self, folder, wait_seconds=0.0, extensions=".png,.jpg,.jpeg,.webp"):
    if not folder or not os.path.isdir(folder):
        raise NotADirectoryError(f"folder not found: {folder!r}")
    exts = tuple(e.strip().lower() for e in extensions.split(",") if e.strip())
    deadline = time.monotonic() + float(wait_seconds)
    while True:
        files = [
            os.path.join(folder, f) for f in os.listdir(folder)
            if f.lower().endswith(exts)
        ]
        if files:
            return (max(files, key=os.path.getmtime),)
        if time.monotonic() >= deadline:
            return ("",)
        time.sleep(0.25)
