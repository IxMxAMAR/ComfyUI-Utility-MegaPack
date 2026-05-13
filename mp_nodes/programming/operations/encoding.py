"""Encoding operations: base64, URL, slug."""

import base64
import re
import urllib.parse

from .. import op


@op(
    op_id="base64_encode",
    display_name="Base64 Encode",
    category="Encoding",
    input_schema={"required": {"text": ("STRING", {"default": ""})}},
    output_indices=(0,),
    description="UTF-8 → base64 (standard, padded).",
)
def base64_encode(self, text):
    return (base64.b64encode(text.encode("utf-8")).decode("ascii"),)


@op(
    op_id="base64_decode",
    display_name="Base64 Decode",
    category="Encoding",
    input_schema={"required": {"text": ("STRING", {"default": ""})}},
    output_indices=(0,),
    description="Base64 → UTF-8 string. Raises on invalid input.",
)
def base64_decode(self, text):
    return (base64.b64decode(text, validate=True).decode("utf-8"),)


@op(
    op_id="url_encode",
    display_name="URL Encode",
    category="Encoding",
    input_schema={"required": {"text": ("STRING", {"default": ""})}},
    output_indices=(0,),
    description="Percent-encode every reserved character (no safe chars).",
)
def url_encode(self, text):
    return (urllib.parse.quote(text, safe=""),)


@op(
    op_id="url_decode",
    display_name="URL Decode",
    category="Encoding",
    input_schema={"required": {"text": ("STRING", {"default": ""})}},
    output_indices=(0,),
    description="Percent-decode (also handles + as space).",
)
def url_decode(self, text):
    return (urllib.parse.unquote_plus(text),)


_SLUG_RE = re.compile(r"[^a-z0-9]+")


@op(
    op_id="slug",
    display_name="Slugify",
    category="Encoding",
    input_schema={
        "required": {
            "text": ("STRING", {"default": ""}),
            "max_length": ("INT", {"default": 80, "min": 1, "max": 1024}),
        }
    },
    output_indices=(0,),
    description="Lowercase, non-alphanumerics → hyphen, trim hyphens, truncate.",
)
def slug(self, text, max_length=80):
    s = _SLUG_RE.sub("-", text.lower()).strip("-")
    return (s[:max_length].rstrip("-"),)
