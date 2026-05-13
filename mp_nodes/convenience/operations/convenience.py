"""Convenience operations: reroute, switch, gate, counter, timer, debug, presets, compare."""

import json as _json
import os
import sys
import time

import torch

from mp_nodes._base import ANY

from .. import op


# -------- module-level state (counters, timers) --------
_COUNTERS: dict[str, int] = {}
_TIMERS: dict[str, float] = {}


@op(
    op_id="reroute_any",
    display_name="Universal Reroute",
    category="Convenience",
    input_schema={"required": {"value": (ANY, {})}},
    output_indices=(0,),
    description="Pass any value straight through. Useful for organizing graph layout.",
)
def reroute_any(self, value):
    return (value,)


@op(
    op_id="multi_split",
    display_name="Multi-Output Split (1→5)",
    category="Convenience",
    input_schema={"required": {"value": (ANY, {})}},
    output_indices=(0, 1, 2, 3, 4),
    description="Send the same value out 5 sockets so you can fan out without rerouting.",
)
def multi_split(self, value):
    return (value, value, value, value, value)


@op(
    op_id="switch_any",
    display_name="Switch (pick by index)",
    category="Convenience",
    input_schema={"required": {
        "index": ("INT", {"default": 0, "min": 0, "max": 4}),
        "value_0": (ANY, {}),
        "value_1": (ANY, {}),
        "value_2": (ANY, {}),
        "value_3": (ANY, {}),
        "value_4": (ANY, {}),
    }},
    output_indices=(0,),
    description="Pass through value_<index>. Modulo wrap-around.",
)
def switch_any(self, index, value_0=None, value_1=None, value_2=None, value_3=None, value_4=None):
    values = [value_0, value_1, value_2, value_3, value_4]
    return (values[int(index) % 5],)


@op(
    op_id="gate_passthrough",
    display_name="Gate (pass if condition)",
    category="Convenience",
    input_schema={"required": {
        "value": (ANY, {}),
        "condition": ("BOOLEAN", {"default": True}),
    }},
    output_indices=(0,),
    description="Returns value if condition is True, otherwise None.",
)
def gate_passthrough(self, value, condition=True):
    return (value if condition else None,)


@op(
    op_id="counter_inc",
    display_name="Counter (increment)",
    category="Convenience",
    input_schema={"required": {
        "key": ("STRING", {"default": "default"}),
        "step": ("INT", {"default": 1}),
        "reset": ("BOOLEAN", {"default": False}),
    }},
    output_indices=(0,),
    description="Per-key counter. Returns the new value after incrementing by `step`.",
)
def counter_inc(self, key, step=1, reset=False):
    if reset:
        _COUNTERS[key] = 0
    _COUNTERS[key] = _COUNTERS.get(key, 0) + int(step)
    return (_COUNTERS[key],)


@op(
    op_id="timer_start",
    display_name="Timer Start",
    category="Convenience",
    input_schema={"required": {"key": ("STRING", {"default": "default"})}},
    output_indices=(0,),
    description="Start a named timer. Returns the start timestamp.",
)
def timer_start(self, key):
    now = time.monotonic()
    _TIMERS[key] = now
    return (now,)


@op(
    op_id="timer_elapsed",
    display_name="Timer Elapsed",
    category="Convenience",
    input_schema={"required": {"key": ("STRING", {"default": "default"})}},
    output_indices=(0,),
    description="Return seconds elapsed since timer_start was called for `key`. -1 if no such timer.",
)
def timer_elapsed(self, key):
    start = _TIMERS.get(key)
    if start is None:
        return (-1.0,)
    return (round(time.monotonic() - start, 6),)


@op(
    op_id="debug_print",
    display_name="Debug Print",
    category="Convenience",
    input_schema={"required": {
        "value": (ANY, {}),
        "label": ("STRING", {"default": "DEBUG"}),
    }},
    output_indices=(0,),
    description="Log value to stderr with label, then pass it through unchanged.",
)
def debug_print(self, value, label="DEBUG"):
    print(f"[{label}] {value!r}", file=sys.stderr, flush=True)
    return (value,)


@op(
    op_id="pin_selector",
    display_name="Pin Selector (pick from saved set)",
    category="Convenience",
    input_schema={"required": {
        "values_json": ("STRING", {"default": '["a","b","c"]', "multiline": True}),
        "index": ("INT", {"default": 0, "min": 0}),
    }},
    output_indices=(0,),
    description="Pick item N from a JSON list. Modulo wraps.",
)
def pin_selector(self, values_json, index=0):
    values = _json.loads(values_json) if values_json else []
    if not isinstance(values, list) or not values:
        return ("",)
    return (values[int(index) % len(values)],)


def _preset_dir() -> str:
    base = os.environ.get("UTILITY_MEGAPACK_PRESET_DIR")
    if base:
        return base
    home = os.path.expanduser("~")
    path = os.path.join(home, ".cache", "comfyui-utility-megapack", "presets")
    os.makedirs(path, exist_ok=True)
    return path


@op(
    op_id="preset_save",
    display_name="Preset Save (named JSON bundle)",
    category="Convenience",
    input_schema={"required": {
        "name": ("STRING", {"default": "default"}),
        "payload_json": ("STRING", {"default": "{}", "multiline": True}),
    }},
    output_indices=(0,),
    description="Save a named JSON bundle to the user preset cache directory.",
)
def preset_save(self, name, payload_json="{}"):
    if not name or "/" in name or "\\" in name:
        raise ValueError("preset name must be non-empty and contain no path separators")
    payload = _json.loads(payload_json) if payload_json else {}
    path = os.path.join(_preset_dir(), f"{name}.json")
    with open(path, "w", encoding="utf-8") as f:
        _json.dump(payload, f, indent=2)
    return (path,)


@op(
    op_id="preset_load",
    display_name="Preset Load (named JSON bundle)",
    category="Convenience",
    input_schema={"required": {"name": ("STRING", {"default": "default"})}},
    output_indices=(0,),
    description="Load a named preset. Returns the JSON payload as a string. Empty string if missing.",
)
def preset_load(self, name):
    if not name or "/" in name or "\\" in name:
        raise ValueError("preset name must be non-empty and contain no path separators")
    path = os.path.join(_preset_dir(), f"{name}.json")
    if not os.path.isfile(path):
        return ("",)
    with open(path, "r", encoding="utf-8") as f:
        return (f.read(),)


@op(
    op_id="compare_side_by_side",
    display_name="Compare Side-by-Side",
    category="Convenience",
    input_schema={"required": {
        "image_a": ("IMAGE", {}),
        "image_b": ("IMAGE", {}),
    }},
    output_indices=(0,),
    description="Concatenate two images horizontally. Smaller is padded with black.",
)
def compare_side_by_side(self, image_a, image_b):
    a, b = image_a, image_b
    if a.shape[0] != b.shape[0]:
        raise ValueError(f"batch mismatch: {a.shape[0]} vs {b.shape[0]}")
    target_h = max(a.shape[1], b.shape[1])

    def pad_to(t, h):
        if t.shape[1] == h:
            return t
        pad = torch.zeros((t.shape[0], h - t.shape[1], t.shape[2], t.shape[3]),
                          dtype=t.dtype, device=t.device)
        return torch.cat([t, pad], dim=1)

    a2 = pad_to(a, target_h)
    b2 = pad_to(b, target_h)
    return (torch.cat([a2, b2], dim=2),)


@op(
    op_id="workflow_note",
    display_name="Workflow Note (annotated passthrough)",
    category="Convenience",
    input_schema={"required": {
        "value": (ANY, {}),
        "note": ("STRING", {"default": "", "multiline": True}),
    }},
    output_indices=(0,),
    description="Pass value through. The note is for human readers of the workflow.",
)
def workflow_note(self, value, note=""):
    return (value,)


@op(
    op_id="value_select",
    display_name="Value Select (5-string switch)",
    category="Convenience",
    input_schema={"required": {
        "index": ("INT", {"default": 0, "min": 0, "max": 4}),
        "v0": ("STRING", {"default": ""}),
        "v1": ("STRING", {"default": ""}),
        "v2": ("STRING", {"default": ""}),
        "v3": ("STRING", {"default": ""}),
        "v4": ("STRING", {"default": ""}),
    }},
    output_indices=(0,),
    description="Pick one of 5 string values by index.",
)
def value_select(self, index, v0="", v1="", v2="", v3="", v4=""):
    return ([v0, v1, v2, v3, v4][int(index) % 5],)
