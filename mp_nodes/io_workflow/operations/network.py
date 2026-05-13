"""HTTP operations: GET, POST."""

import json as _json

import requests

from .. import op


_DEFAULT_TIMEOUT = 30
_MAX_RESPONSE_BYTES = 50 * 1024 * 1024  # 50 MB


@op(
    op_id="http_get",
    display_name="HTTP GET",
    category="Network",
    input_schema={"required": {
        "url": ("STRING", {"default": ""}),
        "timeout_seconds": ("INT", {"default": _DEFAULT_TIMEOUT, "min": 1, "max": 300}),
        "headers_json": ("STRING", {"default": "{}", "multiline": True}),
    }},
    output_indices=(0, 1, 3),
    description="GET request. Returns text, parsed-as-JSON-if-possible, status_code.",
)
def http_get(self, url, timeout_seconds=_DEFAULT_TIMEOUT, headers_json="{}"):
    if not url:
        raise ValueError("url is required")
    headers = _json.loads(headers_json) if headers_json else {}
    resp = requests.get(url, headers=headers, timeout=int(timeout_seconds), stream=True, allow_redirects=True)
    content = b""
    for chunk in resp.iter_content(chunk_size=64 * 1024):
        content += chunk
        if len(content) > _MAX_RESPONSE_BYTES:
            raise ValueError(f"response exceeded {_MAX_RESPONSE_BYTES} bytes")
    text = content.decode(resp.encoding or "utf-8", errors="replace")
    try:
        parsed = _json.loads(text) if text else {}
        if not isinstance(parsed, dict):
            parsed = {"value": parsed}
    except _json.JSONDecodeError:
        parsed = {}
    return (text, parsed, int(resp.status_code))


@op(
    op_id="http_post",
    display_name="HTTP POST (JSON body)",
    category="Network",
    input_schema={"required": {
        "url": ("STRING", {"default": ""}),
        "body_json": ("STRING", {"default": "{}", "multiline": True}),
        "timeout_seconds": ("INT", {"default": _DEFAULT_TIMEOUT, "min": 1, "max": 300}),
        "headers_json": ("STRING", {"default": "{}", "multiline": True}),
    }},
    output_indices=(0, 1, 3),
)
def http_post(self, url, body_json="{}", timeout_seconds=_DEFAULT_TIMEOUT, headers_json="{}"):
    if not url:
        raise ValueError("url is required")
    headers = _json.loads(headers_json) if headers_json else {}
    body = _json.loads(body_json) if body_json else {}
    # stream=True + chunked accumulation so we enforce the size cap BEFORE the
    # full response buffers into memory (Gemini review #2: DoS protection).
    resp = requests.post(url, json=body, headers=headers, timeout=int(timeout_seconds),
                         stream=True, allow_redirects=True)
    content = b""
    for chunk in resp.iter_content(chunk_size=64 * 1024):
        content += chunk
        if len(content) > _MAX_RESPONSE_BYTES:
            raise ValueError(f"response exceeded {_MAX_RESPONSE_BYTES} bytes")
    text = content.decode(resp.encoding or "utf-8", errors="replace")
    try:
        parsed = _json.loads(text) if text else {}
        if not isinstance(parsed, dict):
            parsed = {"value": parsed}
    except _json.JSONDecodeError:
        parsed = {}
    return (text, parsed, int(resp.status_code))
