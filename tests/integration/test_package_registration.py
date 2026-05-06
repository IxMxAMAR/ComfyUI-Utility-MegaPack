"""Integration tests — verify the package registers with ComfyUI's expected protocol."""

import importlib.util
import pathlib

import pytest

PACKAGE_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent


@pytest.fixture(scope="module")
def pkg():
    """Load the root __init__.py via spec_from_file_location.

    Direct `import __init__` is unreliable because Python treats __init__
    as the package-marker name. Loading by file path is explicit and works.
    """
    spec = importlib.util.spec_from_file_location(
        "megapack_pkg",
        PACKAGE_ROOT / "__init__.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_package_exposes_node_class_mappings(pkg):
    assert "UtilMegaPack_SmokeTest" in pkg.NODE_CLASS_MAPPINGS


def test_package_exposes_display_name_mappings(pkg):
    assert "UtilMegaPack_SmokeTest" in pkg.NODE_DISPLAY_NAME_MAPPINGS
    assert pkg.NODE_DISPLAY_NAME_MAPPINGS["UtilMegaPack_SmokeTest"] == "Smoke Test"


def test_package_exposes_web_directory(pkg):
    assert pkg.WEB_DIRECTORY == "./web"


def test_smoke_node_input_types_is_callable(pkg):
    NodeCls = pkg.NODE_CLASS_MAPPINGS["UtilMegaPack_SmokeTest"]
    schema = NodeCls.INPUT_TYPES()
    assert "mode" in schema["required"]
    assert "theme" in schema["required"]
    assert "text" in schema["optional"]


def test_smoke_node_process_returns_padded_tuple(pkg):
    NodeCls = pkg.NODE_CLASS_MAPPINGS["UtilMegaPack_SmokeTest"]
    result = NodeCls().process(mode="echo", theme="(use pack default)", text="round-trip")
    assert isinstance(result, tuple)
    assert len(result) == len(NodeCls.RETURN_TYPES)
    assert result[0] == "round-trip"


def test_smoke_node_has_correct_function_attribute(pkg):
    NodeCls = pkg.NODE_CLASS_MAPPINGS["UtilMegaPack_SmokeTest"]
    assert NodeCls.FUNCTION == "process"


def test_smoke_node_has_correct_category(pkg):
    NodeCls = pkg.NODE_CLASS_MAPPINGS["UtilMegaPack_SmokeTest"]
    assert NodeCls.CATEGORY == "Utility-MegaPack"


def test_smoke_node_return_types_match_return_names(pkg):
    NodeCls = pkg.NODE_CLASS_MAPPINGS["UtilMegaPack_SmokeTest"]
    assert len(NodeCls.RETURN_TYPES) == len(NodeCls.RETURN_NAMES)
