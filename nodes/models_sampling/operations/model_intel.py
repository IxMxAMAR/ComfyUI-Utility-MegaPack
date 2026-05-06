"""Model intelligence: read .safetensors metadata, list installed models, fingerprint, LoRA triggers."""

import hashlib
import json as _json
import os

from .. import op


_MODEL_EXTENSIONS = (".safetensors", ".ckpt", ".pt", ".pth", ".bin")
_FINGERPRINT_PROBE_BYTES = 1024 * 1024  # 1 MB


def _read_safetensors_header(path: str) -> dict:
    """Parse the JSON header of a safetensors file without loading tensors."""
    with open(path, "rb") as f:
        header_len_bytes = f.read(8)
        if len(header_len_bytes) < 8:
            raise ValueError("file too short to be safetensors")
        header_len = int.from_bytes(header_len_bytes, "little")
        if header_len <= 0 or header_len > 100 * 1024 * 1024:
            raise ValueError(f"implausible safetensors header length: {header_len}")
        header_bytes = f.read(header_len)
    return _json.loads(header_bytes)


@op(
    op_id="safetensors_metadata",
    display_name="Read .safetensors Metadata",
    category="Model Intel",
    input_schema={"required": {"path": ("STRING", {"default": ""})}},
    output_indices=(8,),
    description="Returns DICT with the safetensors __metadata__ section (training info, base model, trigger words).",
)
def safetensors_metadata(self, path):
    if not path or not os.path.isfile(path):
        raise FileNotFoundError(f"safetensors file not found: {path!r}")
    header = _read_safetensors_header(path)
    metadata = header.get("__metadata__", {})
    tensor_keys = [k for k in header.keys() if k != "__metadata__"]
    return ({
        "metadata": metadata,
        "tensor_count": len(tensor_keys),
        "tensor_keys_preview": tensor_keys[:10],
        "path": path,
    },)


@op(
    op_id="model_fingerprint",
    display_name="Model Fingerprint (SHA-256 of first 1MB)",
    category="Model Intel",
    input_schema={"required": {"path": ("STRING", {"default": ""})}},
    output_indices=(3,),
    description="Quick hash of the file's first 1 MB. Useful as a cache key without reading the whole model.",
)
def model_fingerprint(self, path):
    if not path or not os.path.isfile(path):
        raise FileNotFoundError(f"file not found: {path!r}")
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read(_FINGERPRINT_PROBE_BYTES))
    return (h.hexdigest(),)


def _list_models_in(folder: str, ext_filter: tuple) -> list[str]:
    if not folder or not os.path.isdir(folder):
        return []
    out = []
    for entry in sorted(os.listdir(folder)):
        full = os.path.join(folder, entry)
        if os.path.isfile(full) and entry.lower().endswith(ext_filter):
            out.append(entry)
    return out


@op(
    op_id="list_installed_models",
    display_name="List Installed Models (folder)",
    category="Model Intel",
    input_schema={"required": {
        "folder": ("STRING", {"default": ""}),
        "extensions": ("STRING", {"default": ".safetensors,.ckpt"}),
    }},
    output_indices=(8,),
    description="Returns DICT with `files` (list) and `count`. Filter by comma-separated extensions.",
)
def list_installed_models(self, folder, extensions=".safetensors,.ckpt"):
    exts = tuple(e.strip().lower() for e in extensions.split(",") if e.strip())
    files = _list_models_in(folder, exts)
    return ({"files": files, "count": len(files), "folder": folder},)


@op(
    op_id="lora_extract_triggers",
    display_name="LoRA — Extract Trigger Words",
    category="Model Intel",
    input_schema={"required": {"path": ("STRING", {"default": ""})}},
    output_indices=(3,),
    description="Read the LoRA's safetensors metadata and extract trigger words from common training keys.",
)
def lora_extract_triggers(self, path):
    if not path or not os.path.isfile(path):
        raise FileNotFoundError(f"lora file not found: {path!r}")
    header = _read_safetensors_header(path)
    metadata = header.get("__metadata__", {}) or {}
    candidates = []
    for key in ("ss_tag_frequency", "ss_dataset_dirs", "trigger_words", "modelspec.trigger_words"):
        v = metadata.get(key)
        if isinstance(v, str) and v.startswith("{"):
            try:
                parsed = _json.loads(v)
                if isinstance(parsed, dict):
                    for inner in parsed.values():
                        if isinstance(inner, dict):
                            candidates.extend(inner.keys())
            except _json.JSONDecodeError:
                pass
        elif isinstance(v, str):
            candidates.extend([t.strip() for t in v.replace(",", " ").split() if t.strip()])
        elif isinstance(v, list):
            candidates.extend(str(t) for t in v)
    # dedupe preserving order
    seen = set()
    triggers = []
    for c in candidates:
        if c not in seen:
            seen.add(c)
            triggers.append(c)
    return (", ".join(triggers),)
