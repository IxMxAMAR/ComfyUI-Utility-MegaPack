"""Control flow primitives: for/while/if/eval/compare/null-coalesce/switch."""

import json

from simpleeval import SimpleEval, NameNotDefined

from .. import op


_MAX_ITERS_HARD_CEILING = 100_000


def _safe_eval(expr: str, names: dict | None = None):
    """Evaluate `expr` via SimpleEval. Reject dunder access. Return the value."""
    if "__" in expr:
        raise ValueError("expression contains forbidden '__' substring")
    s = SimpleEval(names=names or {})
    return s.eval(expr)


@op(
    op_id="for_loop",
    display_name="For Loop",
    category="Control Flow",
    input_schema={"required": {
        "start": ("INT", {"default": 0}),
        "end": ("INT", {"default": 10}),
        "step": ("INT", {"default": 1, "min": 1, "max": 1_000_000}),
    }},
    output_indices=(4,),
    description="Build the list [start, start+step, ..., end-step].",
)
def for_loop(self, start, end, step=1):
    return (list(range(int(start), int(end), int(step))),)


@op(
    op_id="while_loop",
    display_name="While Loop",
    category="Control Flow",
    input_schema={"required": {
        "expr": ("STRING", {"default": "i<10"}),
        "max_iters": ("INT", {"default": 1000, "min": 1, "max": _MAX_ITERS_HARD_CEILING}),
    }},
    output_indices=(4,),
    description="Iterate while `expr` is truthy. `i` is the counter starting at 0. Returns [0, 1, ..., final-1].",
)
def while_loop(self, expr, max_iters=1000):
    cap = min(int(max_iters), _MAX_ITERS_HARD_CEILING)
    out = []
    for i in range(cap):
        if not _safe_eval(expr, {"i": i}):
            break
        out.append(i)
    return (out,)


@op(
    op_id="if_else",
    display_name="If / Else",
    category="Control Flow",
    input_schema={"required": {
        "condition": ("BOOLEAN", {"default": False}),
        "when_true": ("STRING", {"default": ""}),
        "when_false": ("STRING", {"default": ""}),
    }},
    output_indices=(0,),
)
def if_else(self, condition, when_true, when_false):
    return (when_true if bool(condition) else when_false,)


_COMPARE_OPS = {"<": lambda a, b: a < b, ">": lambda a, b: a > b,
                "<=": lambda a, b: a <= b, ">=": lambda a, b: a >= b,
                "==": lambda a, b: a == b, "!=": lambda a, b: a != b}


@op(
    op_id="compare",
    display_name="Compare",
    category="Control Flow",
    input_schema={"required": {
        "a": ("FLOAT", {"default": 0.0}),
        "op": (list(_COMPARE_OPS.keys()), {"default": "=="}),
        "b": ("FLOAT", {"default": 0.0}),
    }},
    output_indices=(3,),
)
def compare(self, a, op, b):
    if op not in _COMPARE_OPS:
        raise ValueError(f"unknown compare op '{op}' (allowed: {list(_COMPARE_OPS)})")
    return (_COMPARE_OPS[op](float(a), float(b)),)


@op(
    op_id="eval_expr",
    display_name="Eval Expression",
    category="Control Flow",
    input_schema={"required": {
        "expr": ("STRING", {"default": "1 + 1"}),
        "vars_json": ("STRING", {"default": "{}"}),
    }},
    output_indices=(6,),
    description="Sandboxed expression evaluator (simpleeval). `vars_json` is parsed as JSON for variable bindings.",
)
def eval_expr(self, expr, vars_json="{}"):
    names = json.loads(vars_json) if vars_json else {}
    if not isinstance(names, dict):
        raise ValueError("vars_json must decode to an object")
    try:
        return (_safe_eval(expr, names),)
    except NameNotDefined as e:
        raise ValueError(f"undefined name in expression: {e}") from e


@op(
    op_id="null_coalesce",
    display_name="Null Coalesce",
    category="Control Flow",
    input_schema={"required": {
        "a": ("STRING", {"default": ""}),
        "b": ("STRING", {"default": ""}),
        "c": ("STRING", {"default": ""}),
    }},
    output_indices=(0,),
    description="Returns the first non-empty string out of a, b, c. Empty if all empty.",
)
def null_coalesce(self, a, b, c=""):
    for v in (a, b, c):
        if v:
            return (v,)
    return ("",)


@op(
    op_id="switch_case",
    display_name="Switch / Case",
    category="Control Flow",
    input_schema={"required": {
        "value": ("STRING", {"default": ""}),
        "cases_json": ("STRING", {"default": '{"_": ""}'}),
    }},
    output_indices=(0,),
    description='cases_json is a JSON object mapping case-string → result-string. "_" is the default.',
)
def switch_case(self, value, cases_json='{"_":""}'):
    cases = json.loads(cases_json) if cases_json else {}
    if not isinstance(cases, dict):
        raise ValueError("cases_json must decode to an object")
    if value in cases:
        return (str(cases[value]),)
    return (str(cases.get("_", "")),)
