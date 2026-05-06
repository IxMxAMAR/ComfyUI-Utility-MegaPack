"""Tests for ConvenienceNode."""

import json

import pytest
import torch

from nodes.convenience import ConvenienceNode


def run(mode, **kwargs):
    return ConvenienceNode().process(mode=mode, theme="(use pack default)", **kwargs)


class TestRouting:
    def test_reroute_passthrough(self):
        assert run("reroute_any", value="hi")[0] == "hi"
        assert run("reroute_any", value=42)[0] == 42

    def test_multi_split_fans_out(self):
        out = run("multi_split", value="x")
        assert out == ("x", "x", "x", "x", "x")

    def test_switch_picks_index(self):
        out = run(
            "switch_any", index=2,
            value_0="a", value_1="b", value_2="c", value_3="d", value_4="e",
        )[0]
        assert out == "c"

    def test_switch_modulo_wraps(self):
        out = run(
            "switch_any", index=7,
            value_0="a", value_1="b", value_2="c", value_3="d", value_4="e",
        )[0]
        assert out == "c"

    def test_gate_passes_when_true(self):
        assert run("gate_passthrough", value="yes", condition=True)[0] == "yes"

    def test_gate_blocks_when_false(self):
        assert run("gate_passthrough", value="yes", condition=False)[0] is None


class TestCounter:
    def test_counter_increments(self):
        # use unique key to avoid leakage between tests
        run("counter_inc", key="test_inc", step=1, reset=True)
        v1 = run("counter_inc", key="test_inc", step=1)[0]
        v2 = run("counter_inc", key="test_inc", step=1)[0]
        assert v2 == v1 + 1

    def test_counter_step_value(self):
        # reset+step=5 in one call: counter starts at 0, then adds 5 -> 5
        out = run("counter_inc", key="test_step", step=5, reset=True)[0]
        assert out == 5

    def test_counter_reset(self):
        run("counter_inc", key="test_reset", step=10)
        run("counter_inc", key="test_reset", step=10)
        out = run("counter_inc", key="test_reset", step=1, reset=True)[0]
        assert out == 1


class TestTimer:
    def test_timer_round_trip(self):
        run("timer_start", key="t1")
        elapsed = run("timer_elapsed", key="t1")[0]
        assert elapsed >= 0.0

    def test_timer_no_such_returns_minus_one(self):
        assert run("timer_elapsed", key="never_started")[0] == -1.0


class TestDebug:
    def test_debug_print_passes_through(self, capsys):
        out = run("debug_print", value=[1, 2, 3], label="X")[0]
        assert out == [1, 2, 3]
        captured = capsys.readouterr()
        assert "[X] [1, 2, 3]" in captured.err


class TestPinSelector:
    def test_pin_basic(self):
        out = run("pin_selector", values_json='["a","b","c"]', index=1)[0]
        assert out == "b"

    def test_pin_modulo(self):
        out = run("pin_selector", values_json='["a","b","c"]', index=7)[0]
        assert out == "b"

    def test_pin_empty(self):
        out = run("pin_selector", values_json='[]', index=0)[0]
        assert out == ""


class TestPresets:
    def test_save_and_load_round_trip(self, tmp_path, monkeypatch):
        monkeypatch.setenv("UTILITY_MEGAPACK_PRESET_DIR", str(tmp_path))
        path = run("preset_save", name="myprefs", payload_json='{"theme":"cyberpunk"}')[0]
        assert path.endswith("myprefs.json")
        loaded = run("preset_load", name="myprefs")[0]
        assert json.loads(loaded) == {"theme": "cyberpunk"}

    def test_load_missing_returns_empty(self, tmp_path, monkeypatch):
        monkeypatch.setenv("UTILITY_MEGAPACK_PRESET_DIR", str(tmp_path))
        out = run("preset_load", name="not-saved")[0]
        assert out == ""

    def test_save_path_separator_rejected(self):
        with pytest.raises(RuntimeError, match="path separators"):
            run("preset_save", name="../sneaky", payload_json="{}")


class TestCompare:
    def test_side_by_side_concatenates_horizontally(self):
        a = torch.zeros((1, 4, 4, 3))
        b = torch.ones((1, 4, 4, 3))
        out = run("compare_side_by_side", image_a=a, image_b=b)[0]
        assert out.shape == (1, 4, 8, 3)
        # left half should be zero
        assert torch.all(out[:, :, :4, :] == 0.0)
        # right half should be one
        assert torch.all(out[:, :, 4:, :] == 1.0)

    def test_side_by_side_pads_height_mismatch(self):
        a = torch.zeros((1, 8, 4, 3))
        b = torch.ones((1, 4, 4, 3))
        out = run("compare_side_by_side", image_a=a, image_b=b)[0]
        assert out.shape == (1, 8, 8, 3)


class TestNoteAndSelect:
    def test_workflow_note_passthrough(self):
        assert run("workflow_note", value="hello", note="this is documentation")[0] == "hello"

    def test_value_select(self):
        out = run("value_select", index=2, v0="a", v1="b", v2="c", v3="d", v4="e")[0]
        assert out == "c"
