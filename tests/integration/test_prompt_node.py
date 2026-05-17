"""End-to-end integration tests for PromptNode."""

import importlib.util
import pathlib

import pytest

PACKAGE_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent


@pytest.fixture(scope="module")
def pkg():
    spec = importlib.util.spec_from_file_location(
        "megapack_pkg",
        PACKAGE_ROOT / "__init__.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_prompt_node_registered(pkg):
    assert "UtilMegaPack_Prompt" in pkg.NODE_CLASS_MAPPINGS
    assert pkg.NODE_DISPLAY_NAME_MAPPINGS["UtilMegaPack_Prompt"] == "Prompt"


def test_prompt_node_has_four_outputs(pkg):
    NodeCls = pkg.NODE_CLASS_MAPPINGS["UtilMegaPack_Prompt"]
    assert NodeCls.RETURN_TYPES == ("STRING", "STRING", "LIST", "INT")
    assert NodeCls.RETURN_NAMES == ("prompt", "negative", "all_prompts", "token_count")


def test_prompt_node_lists_ops(pkg):
    NodeCls = pkg.NODE_CLASS_MAPPINGS["UtilMegaPack_Prompt"]
    schema = NodeCls.INPUT_TYPES()
    options, _ = schema["required"]["mode"]
    # Lower bound — new ops are additive, exact equality was a brittle assertion.
    assert len(options) >= 9, f"expected >=9 ops, got {len(options)}"


def test_prompt_node_smoke_one_per_op_type(pkg):
    NodeCls = pkg.NODE_CLASS_MAPPINGS["UtilMegaPack_Prompt"]
    node = NodeCls()

    # batch
    assert node.process(
        mode="prompt_batch_pick", theme="(use pack default)",
        prompts="a\nb\nc", index=0,
    )[0] == "a"

    # mix
    assert node.process(
        mode="prompt_mix", theme="(use pack default)",
        a="cat", weight_a=1.0, b="dog", weight_b=1.0,
    )[0] == "(cat:1.00) (dog:1.00)"

    # negative auto build
    out = node.process(
        mode="negative_auto_build", theme="(use pack default)",
        positive="x", preset="realistic",
    )
    assert "blurry" in out[1]

    # token count
    assert node.process(
        mode="token_count", theme="(use pack default)",
        text="hello world",
    )[3] == 2
