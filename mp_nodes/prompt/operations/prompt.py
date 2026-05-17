"""Prompt-engineering operations."""

import json
import os
import random
import re

from jinja2 import StrictUndefined
from jinja2.sandbox import SandboxedEnvironment

from .. import op


# SandboxedEnvironment blocks the attribute-walk pivot
# (`__class__.__bases__...`) so a shared workflow can't escalate template
# rendering into Python execution.
_jinja = SandboxedEnvironment(autoescape=False, undefined=StrictUndefined, keep_trailing_newline=False)


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


@op(
    op_id="llm_enhance_prompt",
    display_name="LLM Enhance Prompt (Ollama-compatible)",
    category="Prompt",
    input_schema={"required": {
        "prompt": ("STRING", {"default": "", "multiline": True}),
        "model": ("STRING", {"default": "llama3.2"}),
        "base_url": ("STRING", {"default": "http://127.0.0.1:11434"}),
        "style": (["detailed", "cinematic", "photoreal", "concept_art", "minimal"], {"default": "detailed"}),
        "timeout_seconds": ("INT", {"default": 60, "min": 5, "max": 600}),
    }, "optional": {
        "system_prompt": ("STRING", {"default": "", "multiline": True}),
    }},
    output_indices=(0,),
    description=(
        "Expand a basic prompt into a detailed SD/SDXL prompt via an "
        "Ollama-compatible local LLM endpoint (default: http://127.0.0.1:11434). "
        "Set UTILITY_MEGAPACK_ALLOW_INTERNAL_HTTP=1 to allow loopback. "
        "Other compatible servers (LM Studio, llama.cpp server) also work via "
        "their OpenAI-style /v1/chat/completions endpoint."
    ),
)
def llm_enhance_prompt(self, prompt, model="llama3.2", base_url="http://127.0.0.1:11434",
                      style="detailed", timeout_seconds=60, system_prompt=""):
    import requests
    # Lazy-imported to avoid a circular import at module load.
    from mp_nodes.io_workflow.operations.network import _check_ssrf

    if not prompt.strip():
        return ("",)

    style_directives = {
        "detailed": "Expand into a richly detailed Stable Diffusion prompt. Add lighting, materials, mood, lens, composition. Keep it under 80 tokens.",
        "cinematic": "Rewrite as a cinematic still description: anamorphic lens, dramatic key light, color palette, camera angle. Under 80 tokens.",
        "photoreal": "Rewrite as a photoreal scene: real camera (sensor, lens, ISO), realistic lighting, no painterly terms. Under 80 tokens.",
        "concept_art": "Rewrite as concept art description: medium (oil, ink), brushwork, palette, lighting. Under 80 tokens.",
        "minimal": "Tighten and clarify — no fluff, no adjectives that don't earn their place. Under 30 tokens.",
    }
    system = system_prompt.strip() or (
        "You enhance user prompts for image generators. "
        "Return ONLY the rewritten prompt — no preamble, no quotes, no markdown."
    )
    user_msg = f"{style_directives.get(style, style_directives['detailed'])}\n\nOriginal: {prompt.strip()}"

    base = base_url.rstrip("/")
    _check_ssrf(base)
    # Try Ollama native API first, fall back to OpenAI-compatible.
    try:
        resp = requests.post(
            f"{base}/api/chat",
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_msg},
                ],
                "stream": False,
            },
            timeout=int(timeout_seconds),
        )
        if resp.status_code == 404:
            raise FileNotFoundError("ollama /api/chat 404")
        resp.raise_for_status()
        body = resp.json()
        text = body.get("message", {}).get("content", "")
        if text:
            return (text.strip(),)
    except (requests.RequestException, FileNotFoundError, ValueError):
        pass

    resp = requests.post(
        f"{base}/v1/chat/completions",
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user_msg},
            ],
            "stream": False,
        },
        timeout=int(timeout_seconds),
    )
    resp.raise_for_status()
    body = resp.json()
    choice = (body.get("choices") or [{}])[0]
    text = choice.get("message", {}).get("content", "") or choice.get("text", "")
    return (text.strip(),)
