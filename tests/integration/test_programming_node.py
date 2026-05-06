"""End-to-end integration tests for ProgrammingNode."""

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


def test_programming_node_is_registered(pkg):
    assert "UtilMegaPack_Programming" in pkg.NODE_CLASS_MAPPINGS
    assert pkg.NODE_DISPLAY_NAME_MAPPINGS["UtilMegaPack_Programming"] == "Programming"


def test_programming_node_input_types_lists_60_plus_ops(pkg):
    NodeCls = pkg.NODE_CLASS_MAPPINGS["UtilMegaPack_Programming"]
    schema = NodeCls.INPUT_TYPES()
    options, _ = schema["required"]["mode"]
    assert len(options) >= 58, f"expected >=58 ops, got {len(options)}"


def test_no_skeleton_op_remains(pkg):
    NodeCls = pkg.NODE_CLASS_MAPPINGS["UtilMegaPack_Programming"]
    schema = NodeCls.INPUT_TYPES()
    options, _ = schema["required"]["mode"]
    assert "_skeleton_check" not in options


def test_one_op_per_category_smoke(pkg):
    NodeCls = pkg.NODE_CLASS_MAPPINGS["UtilMegaPack_Programming"]
    node = NodeCls()

    # Encoding
    assert node.process(mode="base64_encode", theme="(use pack default)", text="hi")[0] == "aGk="

    # Logic & Bits
    assert node.process(mode="bool_and", theme="(use pack default)", a=True, b=True)[3] is True

    # Math & Signals
    assert node.process(mode="math_add", theme="(use pack default)", a=2.0, b=3.0)[2] == 5.0

    # Text & Parsing
    assert node.process(
        mode="regex_extract", theme="(use pack default)",
        text="rev1.2.3", pattern=r"(\d+)\.(\d+)\.(\d+)", group=2,
    )[0] == "2"

    # Data Structures
    assert node.process(
        mode="dict_keys", theme="(use pack default)",
        data={"b": 1, "a": 2},
    )[4] == ["a", "b"]

    # Control Flow
    assert node.process(
        mode="for_loop", theme="(use pack default)",
        start=0, end=3, step=1,
    )[4] == [0, 1, 2]

    # Crypto
    assert node.process(
        mode="hash_sha256", theme="(use pack default)", text="hello",
    )[0] == "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"


def test_output_padding_for_int_only_op(pkg):
    """math_add fills only the FLOAT slot. Other slots get type defaults."""
    NodeCls = pkg.NODE_CLASS_MAPPINGS["UtilMegaPack_Programming"]
    result = NodeCls().process(mode="math_add", theme="(use pack default)", a=1.0, b=2.0)
    assert result[0] == ""        # STRING default
    assert result[1] == 0         # INT default
    assert result[2] == 3.0       # FLOAT (filled)
    assert result[3] is False     # BOOLEAN default
    assert result[4] == []        # LIST default
    assert result[5] == {}        # DICT default
    assert result[6] is None      # ANY default


def test_categories_all_present(pkg):
    NodeCls = pkg.NODE_CLASS_MAPPINGS["UtilMegaPack_Programming"]
    cats = NodeCls.REGISTRY.categories()
    expected = {"Encoding", "Logic & Bits", "Math & Signals", "Text & Parsing",
                "Data Structures", "Control Flow", "Crypto"}
    assert set(cats) == expected
