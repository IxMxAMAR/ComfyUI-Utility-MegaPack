"""Tests for _pad_outputs — fills RETURN_TYPES tuple with type-appropriate defaults."""

import pytest
import torch

from mp_nodes._base import ANY, _pad_outputs


def test_filled_indices_use_provided_values():
    result = _pad_outputs(
        op_result=("hello",),
        output_indices=(0,),
        return_types=("STRING", "INT"),
        op_id="echo",
    )
    assert result[0] == "hello"


def test_unfilled_string_defaults_to_empty():
    result = _pad_outputs(
        op_result=(42,),
        output_indices=(1,),
        return_types=("STRING", "INT"),
        op_id="echo",
    )
    assert result[0] == ""


def test_unfilled_int_defaults_to_zero():
    result = _pad_outputs(
        op_result=("x",),
        output_indices=(0,),
        return_types=("STRING", "INT"),
        op_id="echo",
    )
    assert result[1] == 0


def test_unfilled_float_defaults_to_zero():
    result = _pad_outputs(
        op_result=(),
        output_indices=(),
        return_types=("FLOAT",),
        op_id="x",
    )
    assert result[0] == 0.0


def test_unfilled_boolean_defaults_to_false():
    result = _pad_outputs(
        op_result=(),
        output_indices=(),
        return_types=("BOOLEAN",),
        op_id="x",
    )
    assert result[0] is False


def test_unfilled_list_defaults_to_empty_list():
    result = _pad_outputs(
        op_result=(),
        output_indices=(),
        return_types=("LIST",),
        op_id="x",
    )
    assert result[0] == []


def test_unfilled_dict_defaults_to_empty_dict():
    result = _pad_outputs(
        op_result=(),
        output_indices=(),
        return_types=("DICT",),
        op_id="x",
    )
    assert result[0] == {}


def test_unfilled_image_defaults_to_1x1x3_zero_tensor():
    result = _pad_outputs(
        op_result=(),
        output_indices=(),
        return_types=("IMAGE",),
        op_id="x",
    )
    assert isinstance(result[0], torch.Tensor)
    assert result[0].shape == (1, 1, 1, 3)
    assert torch.all(result[0] == 0)


def test_unfilled_mask_defaults_to_1x1_zero_tensor():
    result = _pad_outputs(
        op_result=(),
        output_indices=(),
        return_types=("MASK",),
        op_id="x",
    )
    assert isinstance(result[0], torch.Tensor)
    assert result[0].shape == (1, 1, 1)
    assert torch.all(result[0] == 0)


def test_unfilled_latent_defaults_to_empty_dict():
    """LATENT pads to {} (no 'samples') so downstream sees a clean 'missing samples' error.

    The old hardcoded (1, 4, 8, 8) default broke 16-channel models (Flux/SD3).
    """
    result = _pad_outputs(
        op_result=(),
        output_indices=(),
        return_types=("LATENT",),
        op_id="x",
    )
    assert result[0] == {}


def test_unfilled_wildcard_defaults_to_none():
    result = _pad_outputs(
        op_result=(),
        output_indices=(),
        return_types=(ANY,),
        op_id="x",
    )
    assert result[0] is None


def test_unfilled_opaque_returns_none():
    """Opaque types (MODEL/CLIP/VAE) get None at the padding layer.

    ComfyUI's runtime is responsible for fail-fast when a downstream node
    tries to use None as a model — we don't have wire-level visibility here.
    """
    for opaque in ("MODEL", "CLIP", "VAE"):
        result = _pad_outputs(
            op_result=(),
            output_indices=(),
            return_types=(opaque,),
            op_id="echo",
        )
        assert result == (None,), f"opaque type {opaque} should pad to None"


def test_out_of_range_output_index_raises_value_error():
    """Op author misconfiguration is caught with op_id context, not bare IndexError."""
    with pytest.raises(ValueError, match=r"\[bad_op\] output_indices=\(5,\) is out of range"):
        _pad_outputs(
            op_result=("x",),
            output_indices=(5,),
            return_types=("STRING", "INT"),
            op_id="bad_op",
        )


def test_returns_tuple_matching_return_types_length():
    result = _pad_outputs(
        op_result=("a", 1),
        output_indices=(0, 1),
        return_types=("STRING", "INT", "FLOAT"),
        op_id="x",
    )
    assert isinstance(result, tuple)
    assert len(result) == 3
