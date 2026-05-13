"""Seed management and sampler/scheduler helpers."""

import hashlib
import json as _json
import random as _random

from .. import op


_SAMPLERS = [
    "euler", "euler_ancestral", "heun", "heunpp2",
    "dpm_2", "dpm_2_ancestral", "lms",
    "dpmpp_2m", "dpmpp_2m_sde", "dpmpp_3m_sde",
    "dpmpp_sde", "dpmpp_sde_gpu", "ddim", "uni_pc", "lcm",
]

_SCHEDULERS = [
    "normal", "karras", "exponential", "sgm_uniform",
    "simple", "ddim_uniform", "beta",
]

_SEED_HISTORY: list[int] = []
_SEED_HISTORY_MAX = 32


@op(
    op_id="seed_cycle",
    display_name="Seed Cycle (fixed/incr/decr/random/from-string)",
    category="Seed",
    input_schema={"required": {
        "seed": ("INT", {"default": 0, "min": 0, "max": 0xFFFFFFFF}),
        "cycle_mode": (["fixed", "increment", "decrement", "random", "from_string"], {"default": "fixed"}),
        "string_input": ("STRING", {"default": ""}),
    }},
    output_indices=(5,),
    description="Various seed strategies. from_string deterministically derives a seed from text via SHA-256.",
)
def seed_cycle(self, seed, cycle_mode="fixed", string_input=""):
    out = int(seed)
    if cycle_mode == "increment":
        out = (out + 1) & 0xFFFFFFFF
    elif cycle_mode == "decrement":
        out = (out - 1) & 0xFFFFFFFF
    elif cycle_mode == "random":
        out = _random.SystemRandom().randint(0, 0xFFFFFFFF)
    elif cycle_mode == "from_string":
        digest = hashlib.sha256(string_input.encode("utf-8")).digest()
        out = int.from_bytes(digest[:4], "big")
    _SEED_HISTORY.append(out)
    if len(_SEED_HISTORY) > _SEED_HISTORY_MAX:
        del _SEED_HISTORY[: len(_SEED_HISTORY) - _SEED_HISTORY_MAX]
    return (out,)


@op(
    op_id="multi_seed_batch",
    display_name="Multi-Seed Batch (N seeds)",
    category="Seed",
    input_schema={"required": {
        "base_seed": ("INT", {"default": 0, "min": 0, "max": 0xFFFFFFFF}),
        "count": ("INT", {"default": 4, "min": 1, "max": 256}),
    }},
    output_indices=(8,),
    description="Returns DICT with `seeds` list of N consecutive seeds starting from base_seed.",
)
def multi_seed_batch(self, base_seed, count=4):
    seeds = [(int(base_seed) + i) & 0xFFFFFFFF for i in range(int(count))]
    return ({"seeds": seeds, "count": len(seeds), "base_seed": int(base_seed)},)


@op(
    op_id="seed_history",
    display_name="Seed History (recall recent)",
    category="Seed",
    input_schema={"required": {}},
    output_indices=(8,),
    description="Returns the last 32 seeds emitted by seed_cycle.",
)
def seed_history(self):
    return ({"history": list(_SEED_HISTORY), "count": len(_SEED_HISTORY)},)


@op(
    op_id="sampler_pick",
    display_name="Sampler Picker",
    category="Sampling",
    input_schema={"required": {"sampler": (_SAMPLERS, {"default": "euler"})}},
    output_indices=(4,),
    description="Emit a sampler name as STRING (out:4).",
)
def sampler_pick(self, sampler="euler"):
    return (sampler,)


@op(
    op_id="scheduler_pick",
    display_name="Scheduler Picker",
    category="Sampling",
    input_schema={"required": {"scheduler": (_SCHEDULERS, {"default": "normal"})}},
    output_indices=(3,),
    description="Emit a scheduler name as STRING (out:3 — name slot).",
)
def scheduler_pick(self, scheduler="normal"):
    return (scheduler,)


@op(
    op_id="sampler_params_bundle",
    display_name="Sampler Params Bundle",
    category="Sampling",
    input_schema={"required": {
        "sampler": (_SAMPLERS, {"default": "euler"}),
        "scheduler": (_SCHEDULERS, {"default": "normal"}),
        "steps": ("INT", {"default": 20, "min": 1, "max": 200}),
        "cfg": ("FLOAT", {"default": 7.0, "min": 0.0, "max": 30.0}),
        "denoise": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0}),
    }},
    output_indices=(7, 8),
    description="Bundle sampler+scheduler+steps+cfg+denoise into one DICT (out:8). Also exposes cfg as FLOAT (out:7).",
)
def sampler_params_bundle(self, sampler, scheduler, steps=20, cfg=7.0, denoise=1.0):
    bundle = {
        "sampler": sampler,
        "scheduler": scheduler,
        "steps": int(steps),
        "cfg": float(cfg),
        "denoise": float(denoise),
    }
    return (float(cfg), bundle)
