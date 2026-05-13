"""Tests for MegaPackNodeBase.INPUT_TYPES — the union builder."""

from mp_nodes._base import MegaPackNodeBase, OpRegistry, THEME_CHOICES


def _make_two_op_registry():
    reg = OpRegistry()

    @reg.register(
        op_id="alpha",
        display_name="Alpha",
        category="A",
        input_schema={
            "required": {"a_in": ("STRING", {"default": ""})},
            "optional": {"shared": ("INT", {"default": 0})},
        },
        output_indices=(0,),
    )
    def alpha(self, a_in, shared=0):
        return (a_in,)

    @reg.register(
        op_id="beta",
        display_name="Beta",
        category="B",
        input_schema={
            "required": {"b_in": ("INT", {"default": 0})},
            "optional": {"shared": ("INT", {"default": 0})},
        },
        output_indices=(1,),
    )
    def beta(self, b_in, shared=0):
        return (b_in,)

    return reg


def _make_node_class(reg):
    class _N(MegaPackNodeBase):
        REGISTRY = reg
        RETURN_TYPES = ("STRING", "INT")
        RETURN_NAMES = ("string", "int")
    return _N


def test_input_types_returns_dict_with_required_and_optional():
    reg = _make_two_op_registry()
    NodeCls = _make_node_class(reg)
    schema = NodeCls.INPUT_TYPES()
    assert "required" in schema
    assert "optional" in schema


def test_mode_is_first_required_entry():
    reg = _make_two_op_registry()
    NodeCls = _make_node_class(reg)
    schema = NodeCls.INPUT_TYPES()
    keys = list(schema["required"].keys())
    assert keys[0] == "mode"


def test_theme_is_last_required_entry():
    reg = _make_two_op_registry()
    NodeCls = _make_node_class(reg)
    schema = NodeCls.INPUT_TYPES()
    keys = list(schema["required"].keys())
    assert keys[-1] == "theme"


def test_mode_widget_is_dropdown_of_op_ids():
    reg = _make_two_op_registry()
    NodeCls = _make_node_class(reg)
    schema = NodeCls.INPUT_TYPES()
    mode_def = schema["required"]["mode"]
    options, opts = mode_def
    assert sorted(options) == ["alpha", "beta"]
    assert opts["default"] == "alpha"


def test_theme_widget_uses_theme_choices():
    reg = _make_two_op_registry()
    NodeCls = _make_node_class(reg)
    schema = NodeCls.INPUT_TYPES()
    theme_def = schema["required"]["theme"]
    options, opts = theme_def
    assert options == THEME_CHOICES
    assert opts["default"] == "(use pack default)"


def test_per_op_widgets_land_in_optional():
    reg = _make_two_op_registry()
    NodeCls = _make_node_class(reg)
    schema = NodeCls.INPUT_TYPES()
    assert "a_in" in schema["optional"]
    assert "b_in" in schema["optional"]


def test_shared_widget_is_unioned_once():
    reg = _make_two_op_registry()
    NodeCls = _make_node_class(reg)
    schema = NodeCls.INPUT_TYPES()
    optional_keys = list(schema["optional"].keys())
    assert optional_keys.count("shared") == 1
