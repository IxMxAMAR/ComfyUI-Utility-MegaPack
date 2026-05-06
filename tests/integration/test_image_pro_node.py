"""Integration tests for ImageProNode."""

import importlib.util
import pathlib

import pytest

PACKAGE_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent


@pytest.fixture(scope="module")
def pkg():
    spec = importlib.util.spec_from_file_location("megapack_pkg", PACKAGE_ROOT / "__init__.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_image_pro_node_registered(pkg):
    assert "UtilMegaPack_ImagePro" in pkg.NODE_CLASS_MAPPINGS
    assert pkg.NODE_DISPLAY_NAME_MAPPINGS["UtilMegaPack_ImagePro"] == "Image Pro"


def test_image_pro_node_return_types(pkg):
    NodeCls = pkg.NODE_CLASS_MAPPINGS["UtilMegaPack_ImagePro"]
    assert NodeCls.RETURN_TYPES == ("IMAGE", "MASK", "INT", "INT", "STRING")
    assert NodeCls.RETURN_NAMES == ("image", "mask", "width", "height", "metadata_json")


def test_image_pro_node_lists_25_plus_ops(pkg):
    NodeCls = pkg.NODE_CLASS_MAPPINGS["UtilMegaPack_ImagePro"]
    schema = NodeCls.INPUT_TYPES()
    options, _ = schema["required"]["mode"]
    assert len(options) >= 25, f"expected >=25 ops, got {len(options)}"


def test_image_pro_categories(pkg):
    NodeCls = pkg.NODE_CLASS_MAPPINGS["UtilMegaPack_ImagePro"]
    cats = NodeCls.REGISTRY.categories()
    expected = {"Loaders", "Value & Color", "Spatial", "Style", "Inspect"}
    assert set(cats) == expected
