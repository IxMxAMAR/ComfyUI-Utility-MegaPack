"""Dict and list data-structure operations."""

from .. import op


@op(
    op_id="dict_get",
    display_name="Dict Get",
    category="Data Structures",
    input_schema={"required": {
        "data": ("DICT", {"default": {}}),
        "key": ("STRING", {"default": ""}),
        "default": ("STRING", {"default": ""}),
    }},
    output_indices=(6,),
    description="Returns data[key] if present, otherwise default. Default is a string; pass JSON if you need structured defaults.",
)
def dict_get(self, data, key, default=""):
    if not isinstance(data, dict):
        return (default,)
    return (data.get(key, default),)


@op(
    op_id="dict_set",
    display_name="Dict Set",
    category="Data Structures",
    input_schema={"required": {
        "data": ("DICT", {"default": {}}),
        "key": ("STRING", {"default": ""}),
        "value": ("STRING", {"default": ""}),
    }},
    output_indices=(5,),
    description="Returns a new dict with data[key] = value. Original is not mutated.",
)
def dict_set(self, data, key, value):
    new_data = dict(data) if isinstance(data, dict) else {}
    new_data[key] = value
    return (new_data,)


@op(
    op_id="dict_keys",
    display_name="Dict Keys",
    category="Data Structures",
    input_schema={"required": {"data": ("DICT", {"default": {}})}},
    output_indices=(4,),
    description="Returns sorted list of keys.",
)
def dict_keys(self, data):
    if not isinstance(data, dict):
        return ([],)
    return (sorted(data.keys()),)


@op(
    op_id="dict_values",
    display_name="Dict Values",
    category="Data Structures",
    input_schema={"required": {"data": ("DICT", {"default": {}})}},
    output_indices=(4,),
    description="Returns values in key-sorted order.",
)
def dict_values(self, data):
    if not isinstance(data, dict):
        return ([],)
    return ([data[k] for k in sorted(data.keys())],)


@op(
    op_id="dict_merge",
    display_name="Dict Merge",
    category="Data Structures",
    input_schema={"required": {
        "a": ("DICT", {"default": {}}),
        "b": ("DICT", {"default": {}}),
    }},
    output_indices=(5,),
    description="Shallow merge. b's keys win on conflicts.",
)
def dict_merge(self, a, b):
    out = dict(a) if isinstance(a, dict) else {}
    if isinstance(b, dict):
        out.update(b)
    return (out,)


@op(
    op_id="list_length",
    display_name="List Length",
    category="Data Structures",
    input_schema={"required": {"data": ("LIST", {"default": []})}},
    output_indices=(1,),
)
def list_length(self, data):
    return (len(data),)


@op(
    op_id="list_index",
    display_name="List Index",
    category="Data Structures",
    input_schema={"required": {
        "data": ("LIST", {"default": []}),
        "index": ("INT", {"default": 0}),
    }},
    output_indices=(6,),
    description="Negative indexes supported. Raises IndexError on out-of-range.",
)
def list_index(self, data, index):
    if not data:
        raise IndexError("list is empty")
    return (data[index],)


@op(
    op_id="list_slice",
    display_name="List Slice",
    category="Data Structures",
    input_schema={"required": {
        "data": ("LIST", {"default": []}),
        "start": ("INT", {"default": 0}),
        "stop": ("INT", {"default": 0}),
    }},
    output_indices=(4,),
    description="stop = 0 means 'to end'.",
)
def list_slice(self, data, start=0, stop=0):
    end = len(data) if stop == 0 else stop
    return (list(data[start:end]),)


@op(
    op_id="list_sort",
    display_name="List Sort",
    category="Data Structures",
    input_schema={"required": {
        "data": ("LIST", {"default": []}),
        "reverse": ("BOOLEAN", {"default": False}),
    }},
    output_indices=(4,),
    description="Sorts by string repr (so mixed-type lists don't crash).",
)
def list_sort(self, data, reverse=False):
    return (sorted(data, key=str, reverse=bool(reverse)),)


@op(
    op_id="list_reverse",
    display_name="List Reverse",
    category="Data Structures",
    input_schema={"required": {"data": ("LIST", {"default": []})}},
    output_indices=(4,),
)
def list_reverse(self, data):
    return (list(reversed(data)),)
