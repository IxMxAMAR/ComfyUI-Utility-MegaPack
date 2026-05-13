"""Tests for ModelsSamplingNode."""

import json
import struct

import pytest

from mp_nodes.models_sampling import ModelsSamplingNode


def run(mode, **kwargs):
    return ModelsSamplingNode().process(mode=mode, theme="(use pack default)", **kwargs)


def _make_safetensors(tmp_path, name, metadata=None, tensor_keys=None):
    """Create a minimal valid safetensors file with the given metadata block."""
    header = {}
    if metadata is not None:
        header["__metadata__"] = metadata
    for k in tensor_keys or []:
        header[k] = {"dtype": "F32", "shape": [1], "data_offsets": [0, 4]}
    header_bytes = json.dumps(header).encode("utf-8")
    # Pad to 8-byte alignment
    pad = (8 - len(header_bytes) % 8) % 8
    header_bytes += b" " * pad
    body = b"\x00\x00\x00\x00" * len(tensor_keys or [])
    path = tmp_path / name
    with open(path, "wb") as f:
        f.write(struct.pack("<Q", len(header_bytes)))
        f.write(header_bytes)
        f.write(body)
    return str(path)


class TestModelIntel:
    def test_safetensors_metadata(self, tmp_path):
        path = _make_safetensors(
            tmp_path, "model.safetensors",
            metadata={"author": "test", "trigger_words": "cat dog"},
            tensor_keys=["w0", "w1", "w2"],
        )
        info = run("safetensors_metadata", path=path)[8]
        assert info["metadata"]["author"] == "test"
        assert info["tensor_count"] == 3

    def test_safetensors_metadata_missing_file(self):
        with pytest.raises(RuntimeError, match="not found"):
            run("safetensors_metadata", path="/no/such/file.safetensors")

    def test_model_fingerprint_is_deterministic(self, tmp_path):
        path = tmp_path / "x.safetensors"
        path.write_bytes(b"hello world" * 1000)
        a = run("model_fingerprint", path=str(path))[3]
        b = run("model_fingerprint", path=str(path))[3]
        assert a == b
        assert len(a) == 64  # sha256 hex

    def test_list_installed_models(self, tmp_path):
        for name in ("a.safetensors", "b.safetensors", "c.txt"):
            (tmp_path / name).write_text("x")
        info = run("list_installed_models", folder=str(tmp_path), extensions=".safetensors")[8]
        assert info["count"] == 2
        assert "a.safetensors" in info["files"]
        assert "c.txt" not in info["files"]

    def test_list_installed_models_missing_folder(self):
        info = run("list_installed_models", folder="/nope", extensions=".safetensors")[8]
        assert info["count"] == 0

    def test_lora_extract_triggers(self, tmp_path):
        path = _make_safetensors(
            tmp_path, "lora.safetensors",
            metadata={"trigger_words": "cat, dog, bird"},
        )
        triggers = run("lora_extract_triggers", path=path)[3]
        assert "cat" in triggers
        assert "dog" in triggers


class TestResolution:
    def test_aspect_ratio_16_9(self):
        out = run("aspect_ratio_pick", preset="16:9", long_side=1024)
        assert out[5] == 1024  # width
        assert out[6] == 576   # height

    def test_aspect_ratio_portrait(self):
        out = run("aspect_ratio_pick", preset="9:16 (portrait)", long_side=1024)
        assert out[5] == 576   # width
        assert out[6] == 1024  # height

    def test_aspect_ratio_square(self):
        out = run("aspect_ratio_pick", preset="1:1 (square)", long_side=512)
        assert out[5] == 512 and out[6] == 512

    def test_sdxl_bucket_index_zero(self):
        out = run("sdxl_bucket_pick", index=0)
        assert (out[5], out[6]) == (1024, 1024)

    def test_sdxl_bucket_index_wraps(self):
        out = run("sdxl_bucket_pick", index=11)  # 11 % 9 = 2
        assert (out[5], out[6]) == (896, 1152)

    def test_snap_to_multiple(self):
        assert run("snap_to_multiple", value=1023, multiple=64)[5] == 1024
        assert run("snap_to_multiple", value=999, multiple=8)[5] == 1000
        assert run("snap_to_multiple", value=1024, multiple=64)[5] == 1024

    def test_megapixel_calculator_1mp_16_9(self):
        out = run("megapixel_calculator", target_megapixels=1.0, ratio_w=16, ratio_h=9, snap_multiple=8)
        # ~ 1MP at 16:9 = 1336 × 752 (snapped)
        actual_mp = out[8]["actual_megapixels"]
        assert 0.9 <= actual_mp <= 1.1


class TestSeed:
    def test_seed_fixed_returns_input(self):
        assert run("seed_cycle", seed=42, cycle_mode="fixed", string_input="")[5] == 42

    def test_seed_increment(self):
        assert run("seed_cycle", seed=99, cycle_mode="increment", string_input="")[5] == 100

    def test_seed_decrement(self):
        assert run("seed_cycle", seed=99, cycle_mode="decrement", string_input="")[5] == 98

    def test_seed_from_string_deterministic(self):
        a = run("seed_cycle", seed=0, cycle_mode="from_string", string_input="hello")[5]
        b = run("seed_cycle", seed=0, cycle_mode="from_string", string_input="hello")[5]
        assert a == b
        assert 0 <= a <= 0xFFFFFFFF

    def test_seed_from_string_changes_with_input(self):
        a = run("seed_cycle", seed=0, cycle_mode="from_string", string_input="hello")[5]
        b = run("seed_cycle", seed=0, cycle_mode="from_string", string_input="world")[5]
        assert a != b

    def test_multi_seed_batch(self):
        out = run("multi_seed_batch", base_seed=100, count=4)[8]
        assert out["seeds"] == [100, 101, 102, 103]
        assert out["count"] == 4

    def test_seed_history_records(self):
        run("seed_cycle", seed=1, cycle_mode="fixed")
        run("seed_cycle", seed=2, cycle_mode="fixed")
        info = run("seed_history")[8]
        assert info["count"] >= 2
        assert info["history"][-1] == 2


class TestSampling:
    def test_sampler_pick(self):
        assert run("sampler_pick", sampler="euler")[4] == "euler"

    def test_scheduler_pick(self):
        assert run("scheduler_pick", scheduler="karras")[3] == "karras"

    def test_sampler_params_bundle(self):
        out = run("sampler_params_bundle", sampler="dpmpp_2m", scheduler="karras",
                  steps=30, cfg=8.0, denoise=0.8)
        assert out[7] == 8.0  # cfg as FLOAT
        bundle = out[8]
        assert bundle["sampler"] == "dpmpp_2m"
        assert bundle["scheduler"] == "karras"
        assert bundle["steps"] == 30
        assert bundle["denoise"] == 0.8


class TestOpaqueOutputs:
    """ModelsSamplingNode has MODEL/CLIP/VAE in RETURN_TYPES. None of our ops fill them.
    Verify they pad to None (not raise)."""

    def test_unfilled_opaque_outputs_are_none(self):
        out = run("sampler_pick", sampler="euler")
        # MODEL/CLIP/VAE are at indices 0, 1, 2
        assert out[0] is None
        assert out[1] is None
        assert out[2] is None
