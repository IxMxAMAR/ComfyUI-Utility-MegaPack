"""Prompt-engineering operations."""

import json
import os
import random
import re

from jinja2 import Environment, StrictUndefined

from .. import op


_jinja = Environment(autoescape=False, undefined=StrictUndefined, keep_trailing_newline=False)


_NEGATIVE_PRESETS = {
    "realistic": "blurry, lowres, bad anatomy, watermark, signature, text",
    "anime": "low quality, bad hands, blurry, watermark, signature, jpeg artifacts",
    "landscape": "people, person, watermark, blurry, oversaturated",
    "none": "",
}


@op(
    op_id="prompt_batch_pick",
    display_name="Prompt Batch (pick by index)",
    category="Prompt",
    input_schema={"required": {
        "prompts": ("STRING", {"default": "", "multiline": True}),
        "index": ("INT", {"default": 0}),
    }},
    output_indices=(0, 2),
    description="Splits multi-line input into a list, picks index (modulo wrap-around). Returns picked + full list.",
)
def prompt_batch_pick(self, prompts, index=0):
    lines = [ln.strip() for ln in prompts.splitlines() if ln.strip()]
    if not lines:
        return ("", [])
    return (lines[index % len(lines)], lines)


@op(
    op_id="prompt_from_file",
    display_name="Load Prompts from File",
    category="Prompt",
    input_schema={"required": {
        "path": ("STRING", {"default": ""}),
        "index": ("INT", {"default": 0}),
        "seed": ("INT", {"default": -1, "min": -1, "max": 0xFFFFFFFF}),
    }},
    output_indices=(0, 2),
    description="Load .txt/.csv (one prompt per line). seed >= 0 picks randomly; seed = -1 uses index.",
)
def prompt_from_file(self, path, index=0, seed=-1):
    if not path or not os.path.isfile(path):
        raise FileNotFoundError(f"prompt file not found: {path!r}")
    with open(path, "r", encoding="utf-8") as f:
        lines = [ln.strip() for ln in f if ln.strip() and not ln.lstrip().startswith("#")]
    if not lines:
        return ("", [])
    if seed >= 0:
        rng = random.Random(seed)
        return (rng.choice(lines), lines)
    return (lines[index % len(lines)], lines)


_WILDCARD_RE = re.compile(r"__([a-zA-Z_][a-zA-Z0-9_]*)__")


@op(
    op_id="wildcard_expand",
    display_name="Wildcard Expand (__key__)",
    category="Prompt",
    input_schema={"required": {
        "text": ("STRING", {"default": "", "multiline": True}),
        "wildcards_json": ("STRING", {"default": "{}", "multiline": True}),
        "seed": ("INT", {"default": -1, "min": -1, "max": 0xFFFFFFFF}),
    }},
    output_indices=(0,),
    description='Replace each __key__ with a random pick from wildcards_json[key]. Each occurrence is sampled independently.',
)
def wildcard_expand(self, text, wildcards_json="{}", seed=-1):
    pools = json.loads(wildcards_json) if wildcards_json else {}
    if not isinstance(pools, dict):
        raise ValueError("wildcards_json must decode to an object")
    rng = random.Random() if seed == -1 else random.Random(seed)

    def replace(match):
        key = match.group(1)
        choices = pools.get(key)
        if not choices:
            return match.group(0)
        return str(rng.choice(choices))

    return (_WILDCARD_RE.sub(replace, text),)


@op(
    op_id="prompt_mix",
    display_name="Prompt Mix (weighted)",
    category="Prompt",
    input_schema={"required": {
        "a": ("STRING", {"default": "", "multiline": True}),
        "weight_a": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 5.0}),
        "b": ("STRING", {"default": "", "multiline": True}),
        "weight_b": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 5.0}),
    }},
    output_indices=(0,),
    description='Returns "(a:weight_a) (b:weight_b)" — Auto1111 attention syntax.',
)
def prompt_mix(self, a, weight_a, b, weight_b):
    parts = []
    if a:
        parts.append(f"({a}:{float(weight_a):.2f})")
    if b:
        parts.append(f"({b}:{float(weight_b):.2f})")
    return (" ".join(parts),)


@op(
    op_id="prompt_template_render",
    display_name="Prompt Template (Jinja2)",
    category="Prompt",
    input_schema={"required": {
        "template": ("STRING", {"default": "", "multiline": True}),
        "vars_json": ("STRING", {"default": "{}", "multiline": True}),
    }},
    output_indices=(0,),
)
def prompt_template_render(self, template, vars_json="{}"):
    variables = json.loads(vars_json) if vars_json else {}
    if not isinstance(variables, dict):
        raise ValueError("vars_json must decode to an object")
    return (_jinja.from_string(template).render(**variables),)


@op(
    op_id="prompt_clean",
    display_name="Prompt Clean",
    category="Prompt",
    input_schema={"required": {
        "text": ("STRING", {"default": "", "multiline": True}),
        "dedupe": ("BOOLEAN", {"default": True}),
    }},
    output_indices=(0,),
    description="Collapse whitespace, fix double-commas, optionally dedupe comma-separated phrases.",
)
def prompt_clean(self, text, dedupe=True):
    # Collapse whitespace
    s = re.sub(r"\s+", " ", text).strip()
    # Fix multiple commas
    s = re.sub(r",\s*,+", ",", s)
    # Normalize spacing around commas
    s = re.sub(r"\s*,\s*", ", ", s)
    s = s.strip(", ").strip()
    if dedupe:
        seen = set()
        kept = []
        for phrase in s.split(", "):
            normalized = phrase.strip().lower()
            if normalized and normalized not in seen:
                seen.add(normalized)
                kept.append(phrase.strip())
        s = ", ".join(kept)
    return (s,)


@op(
    op_id="negative_auto_build",
    display_name="Negative — Auto Build",
    category="Prompt",
    input_schema={"required": {
        "positive": ("STRING", {"default": "", "multiline": True}),
        "preset": (list(_NEGATIVE_PRESETS.keys()), {"default": "realistic"}),
    }},
    output_indices=(1,),
    description="Generate a negative prompt from a preset. Positive is accepted for downstream pairing but not modified.",
)
def negative_auto_build(self, positive, preset="realistic"):
    return (_NEGATIVE_PRESETS.get(preset, ""),)


_PUNCT = set(",.!?;:'\"-()[]{}")


@op(
    op_id="token_count",
    display_name="Token Count (approximate)",
    category="Prompt",
    input_schema={"required": {"text": ("STRING", {"default": "", "multiline": True})}},
    output_indices=(3,),
    description="Approximate CLIP token count (word + punctuation heuristic). Warn at 75/150 in your workflow.",
)
def token_count(self, text):
    if not text:
        return (0,)
    words = re.findall(r"\S+", text)
    punct = sum(1 for ch in text if ch in _PUNCT)
    return (len(words) + punct,)


@op(
    op_id="prompt_join_list",
    display_name="Join Prompts",
    category="Prompt",
    input_schema={"required": {
        "prompts": ("LIST", {"default": []}),
        "separator": ("STRING", {"default": ", "}),
    }},
    output_indices=(0,),
)
def prompt_join_list(self, prompts, separator=", "):
    return (separator.join(str(p) for p in (prompts or [])),)
