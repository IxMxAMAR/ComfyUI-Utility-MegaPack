"""Text processing, regex, templating, parsing."""

import json
import re

import yaml
from jinja2 import StrictUndefined
from jinja2.sandbox import SandboxedEnvironment

from .. import op


# SandboxedEnvironment blocks attribute-walks like
# `{{ obj.__class__.__bases__[0].__subclasses__() }}` that would otherwise let a
# shared workflow pivot from string templating into arbitrary Python exec/RCE.
_jinja_env = SandboxedEnvironment(
    autoescape=False,
    undefined=StrictUndefined,
    keep_trailing_newline=False,
)


@op(
    op_id="regex_match",
    display_name="Regex Match",
    category="Text & Parsing",
    input_schema={"required": {
        "text": ("STRING", {"default": ""}),
        "pattern": ("STRING", {"default": ""}),
    }},
    output_indices=(3,),
    description="True if `pattern` matches anywhere in `text`.",
)
def regex_match(self, text, pattern):
    return (re.search(pattern, text) is not None,)


@op(
    op_id="regex_extract",
    display_name="Regex Extract",
    category="Text & Parsing",
    input_schema={"required": {
        "text": ("STRING", {"default": ""}),
        "pattern": ("STRING", {"default": ""}),
        "group": ("INT", {"default": 0, "min": 0, "max": 99}),
    }},
    output_indices=(0,),
    description="Returns the matched group, or '' if no match.",
)
def regex_extract(self, text, pattern, group=0):
    m = re.search(pattern, text)
    if m is None:
        return ("",)
    if group > 0 and group > (m.lastindex or 0):
        return ("",)
    return (m.group(group),)


@op(
    op_id="regex_replace",
    display_name="Regex Replace",
    category="Text & Parsing",
    input_schema={"required": {
        "text": ("STRING", {"default": ""}),
        "pattern": ("STRING", {"default": ""}),
        "replacement": ("STRING", {"default": ""}),
    }},
    output_indices=(0,),
)
def regex_replace(self, text, pattern, replacement):
    return (re.sub(pattern, replacement, text),)


@op(
    op_id="regex_split",
    display_name="Regex Split",
    category="Text & Parsing",
    input_schema={"required": {
        "text": ("STRING", {"default": ""}),
        "pattern": ("STRING", {"default": r"\s+"}),
        "max_splits": ("INT", {"default": 0, "min": 0, "max": 1024}),
    }},
    output_indices=(4,),
    description="max_splits = 0 means unlimited.",
)
def regex_split(self, text, pattern, max_splits=0):
    return (re.split(pattern, text, maxsplit=max_splits),)


@op(
    op_id="template_render",
    display_name="Template Render (Jinja2)",
    category="Text & Parsing",
    input_schema={"required": {
        "template": ("STRING", {"default": "", "multiline": True}),
        "vars_json": ("STRING", {"default": "{}"}),
    }},
    output_indices=(0,),
    description="Render Jinja2 template with vars from JSON.",
)
def template_render(self, template, vars_json="{}"):
    variables = json.loads(vars_json) if vars_json else {}
    if not isinstance(variables, dict):
        raise ValueError("vars_json must decode to an object")
    return (_jinja_env.from_string(template).render(**variables),)


@op(
    op_id="string_concat",
    display_name="String Concat",
    category="Text & Parsing",
    input_schema={"required": {
        "a": ("STRING", {"default": ""}),
        "b": ("STRING", {"default": ""}),
        "sep": ("STRING", {"default": ""}),
    }},
    output_indices=(0,),
)
def string_concat(self, a, b, sep=""):
    return (f"{a}{sep}{b}",)


@op(
    op_id="string_upper",
    display_name="String Upper",
    category="Text & Parsing",
    input_schema={"required": {"text": ("STRING", {"default": ""})}},
    output_indices=(0,),
)
def string_upper(self, text):
    return (text.upper(),)


@op(
    op_id="string_lower",
    display_name="String Lower",
    category="Text & Parsing",
    input_schema={"required": {"text": ("STRING", {"default": ""})}},
    output_indices=(0,),
)
def string_lower(self, text):
    return (text.lower(),)


@op(
    op_id="string_trim",
    display_name="String Trim",
    category="Text & Parsing",
    input_schema={"required": {"text": ("STRING", {"default": ""})}},
    output_indices=(0,),
)
def string_trim(self, text):
    return (text.strip(),)


@op(
    op_id="tokenize_words",
    display_name="Tokenize Words",
    category="Text & Parsing",
    input_schema={"required": {"text": ("STRING", {"default": ""})}},
    output_indices=(4,),
    description="Naive whitespace split.",
)
def tokenize_words(self, text):
    return (text.split(),)


@op(
    op_id="yaml_parse",
    display_name="YAML Parse",
    category="Text & Parsing",
    input_schema={"required": {"text": ("STRING", {"default": "", "multiline": True})}},
    output_indices=(5,),
    description="YAML → dict. Empty input returns empty dict. Top-level non-mapping is wrapped under 'value'.",
)
def yaml_parse(self, text):
    if not text.strip():
        return ({},)
    parsed = yaml.safe_load(text)
    if parsed is None:
        return ({},)
    if isinstance(parsed, dict):
        return (parsed,)
    return ({"value": parsed},)


@op(
    op_id="yaml_dump",
    display_name="YAML Dump",
    category="Text & Parsing",
    input_schema={"required": {"data_json": ("STRING", {"default": "{}", "multiline": True})}},
    output_indices=(0,),
    description="JSON → YAML.",
)
def yaml_dump(self, data_json="{}"):
    data = json.loads(data_json) if data_json else {}
    return (yaml.safe_dump(data, sort_keys=False, default_flow_style=False).rstrip("\n") + "\n",)
