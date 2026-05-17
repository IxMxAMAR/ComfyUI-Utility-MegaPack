"""HTTP operations: GET, POST."""

import ipaddress
import json as _json
import os
import socket
from urllib.parse import urlparse

import requests

from .. import op


_DEFAULT_TIMEOUT = 30
_MAX_RESPONSE_BYTES = 50 * 1024 * 1024  # 50 MB
_SSRF_ESCAPE_ENV = "UTILITY_MEGAPACK_ALLOW_INTERNAL_HTTP"


def _is_internal_address(host: str) -> bool:
    """True if the host resolves to a loopback / private / link-local address.

    Catches:
      - localhost, 127.0.0.0/8, ::1
      - RFC1918 (10/8, 172.16/12, 192.168/16)
      - link-local 169.254/16 (AWS/GCP metadata endpoint lives here!)
      - reserved / multicast / private-CGN ranges
    """
    if not host:
        return True
    try:
        # gethostbyname_ex returns all A records for a hostname so we can't be
        # bypassed by a DNS name that resolves to a private IP.
        _, _, addrs = socket.gethostbyname_ex(host)
    except OSError:
        return False
    for addr in addrs:
        try:
            ip = ipaddress.ip_address(addr)
        except ValueError:
            continue
        if (ip.is_loopback or ip.is_private or ip.is_link_local
                or ip.is_multicast or ip.is_reserved or ip.is_unspecified):
            return True
    return False


def _check_ssrf(url: str) -> None:
    """Reject requests to internal addresses unless explicitly allowed.

    The cloud-metadata endpoint at 169.254.169.254 is the classic SSRF target
    — a shared workflow that hits it can dump IAM credentials on EC2/GCE.
    Set UTILITY_MEGAPACK_ALLOW_INTERNAL_HTTP=1 to access localhost services
    (e.g. local Ollama).
    """
    if os.environ.get(_SSRF_ESCAPE_ENV) == "1":
        return
    try:
        host = urlparse(url).hostname
    except Exception:
        host = None
    if host and _is_internal_address(host):
        raise PermissionError(
            f"http to internal address blocked: {host!r}. "
            f"Set {_SSRF_ESCAPE_ENV}=1 if this is intentional (e.g. local Ollama)."
        )


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
    _check_ssrf(url)
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
    _check_ssrf(url)
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
