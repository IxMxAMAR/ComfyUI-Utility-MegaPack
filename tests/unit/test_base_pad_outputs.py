"""Tests for _pad_outputs — fills RETURN_TYPES tuple with type-appropriate defaults."""

import pytest
import torch

from nodes._base import ANY, OutputNotProducedError, _pad_outputs


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


def test_unfilled_latent_defaults_to_empty_4_8_8():
    result = _pad_outputs(
        op_result=(),
        output_indices=(),
        return_types=("LATENT",),
        op_id="x",
    )
    assert isinstance(result[0], dict)
    assert "samples" in result[0]
    assert result[0]["samples"].shape == (1, 4, 8, 8)


def test_unfilled_wildcard_defaults_to_none():
    result = _pad_outputs(
        op_result=(),
        output_indices=(),
        return_types=(ANY,),
        op_id="x",
    )
    assert result[0] is None


def test_unfilled_model_raises():
    with pytest.raises(OutputNotProducedError) as exc:
        _pad_outputs(
            op_result=(),
            output_indices=(),
            return_types=("MODEL",),
            op_id="echo",
        )
    assert exc.value.slot_name == "MODEL"
    assert exc.value.op_id == "echo"


def test_unfilled_clip_raises():
    with pytest.raises(OutputNotProducedError):
        _pad_outputs(
            op_result=(),
            output_indices=(),
            return_types=("CLIP",),
            op_id="echo",
        )


def test_unfilled_vae_raises():
    with pytest.raises(OutputNotProducedError):
        _pad_outputs(
            op_result=(),
            output_indices=(),
            return_types=("VAE",),
            op_id="echo",
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
