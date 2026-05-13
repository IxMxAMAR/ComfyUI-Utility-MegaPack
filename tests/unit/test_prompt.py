"""Tests for PromptNode operations."""

import os
import tempfile

import pytest

from mp_nodes.prompt import PromptNode


def run(mode, **kwargs):
    return PromptNode().process(mode=mode, theme="(use pack default)", **kwargs)


class TestBatchPick:
    def test_in_range(self):
        out = run("prompt_batch_pick", prompts="a\nb\nc", index=1)
        assert out[0] == "b"
        assert out[2] == ["a", "b", "c"]

    def test_modulo_wraps(self):
        out = run("prompt_batch_pick", prompts="a\nb\nc", index=5)
        assert out[0] == "c"

    def test_empty_input(self):
        out = run("prompt_batch_pick", prompts="", index=0)
        assert out[0] == ""
        assert out[2] == []

    def test_strips_blank_lines(self):
        out = run("prompt_batch_pick", prompts="a\n\n\nb", index=1)
        assert out[0] == "b"


class TestFromFile:
    def test_round_trip(self, tmp_path):
        f = tmp_path / "prompts.txt"
        f.write_text("alpha\n# comment\nbeta\ngamma\n", encoding="utf-8")
        out = run("prompt_from_file", path=str(f), index=2)
        assert out[0] == "gamma"
        assert out[2] == ["alpha", "beta", "gamma"]

    def test_seeded_random(self, tmp_path):
        f = tmp_path / "p.txt"
        f.write_text("a\nb\nc\nd\ne\n", encoding="utf-8")
        out_a = run("prompt_from_file", path=str(f), seed=42)
        out_b = run("prompt_from_file", path=str(f), seed=42)
        assert out_a[0] == out_b[0]

    def test_missing_file_raises(self):
        with pytest.raises(RuntimeError, match="not found"):
            run("prompt_from_file", path="/nope/nowhere.txt")


class TestWildcardExpand:
    def test_basic_seeded(self):
        out = run(
            "wildcard_expand",
            text="a __color__ car",
            wildcards_json='{"color": ["red", "blue", "green"]}',
            seed=42,
        )[0]
        # Same seed = same output
        out2 = run(
            "wildcard_expand",
            text="a __color__ car",
            wildcards_json='{"color": ["red", "blue", "green"]}',
            seed=42,
        )[0]
        assert out == out2
        assert out.startswith("a ") and out.endswith(" car")

    def test_unknown_key_passthrough(self):
        out = run(
            "wildcard_expand",
            text="a __unknown__ thing",
            wildcards_json='{"color": ["red"]}',
            seed=1,
        )[0]
        assert "__unknown__" in out

    def test_invalid_json_raises(self):
        with pytest.raises(RuntimeError):
            run("wildcard_expand", text="x", wildcards_json="not json")


class TestPromptMix:
    def test_basic_format(self):
        out = run("prompt_mix", a="cat", weight_a=1.5, b="dog", weight_b=0.5)[0]
        assert out == "(cat:1.50) (dog:0.50)"

    def test_empty_a(self):
        out = run("prompt_mix", a="", weight_a=1.0, b="dog", weight_b=1.0)[0]
        assert out == "(dog:1.00)"


class TestTemplateRender:
    def test_basic(self):
        out = run("prompt_template_render", template="hi {{n}}", vars_json='{"n":"world"}')[0]
        assert out == "hi world"


class TestPromptClean:
    def test_collapses_whitespace(self):
        assert run("prompt_clean", text="hello    world", dedupe=False)[0] == "hello world"

    def test_normalizes_commas(self):
        assert run("prompt_clean", text="cat,,dog", dedupe=False)[0] == "cat, dog"

    def test_dedupe_removes_duplicates(self):
        assert run("prompt_clean", text="cat, cat, dog", dedupe=True)[0] == "cat, dog"

    def test_dedupe_off_keeps_duplicates(self):
        assert run("prompt_clean", text="cat, cat, dog", dedupe=False)[0] == "cat, cat, dog"

    def test_strips_leading_trailing(self):
        assert run("prompt_clean", text="  ,, hello ,, ", dedupe=False)[0] == "hello"


class TestNegativeAutoBuild:
    def test_realistic_preset(self):
        out = run("negative_auto_build", positive="cat", preset="realistic")[1]
        assert "blurry" in out

    def test_anime_preset(self):
        out = run("negative_auto_build", positive="cat", preset="anime")[1]
        assert "low quality" in out

    def test_none_preset_returns_empty(self):
        out = run("negative_auto_build", positive="cat", preset="none")[1]
        assert out == ""


class TestTokenCount:
    def test_empty(self):
        assert run("token_count", text="")[3] == 0

    def test_single_word(self):
        assert run("token_count", text="hello")[3] == 1

    def test_words_plus_punctuation(self):
        # "hello world." -> 2 words + 1 period = 3
        assert run("token_count", text="hello world.")[3] == 3

    def test_whitespace_does_not_count(self):
        assert run("token_count", text="   hello   world   ")[3] == 2


class TestJoinList:
    def test_basic(self):
        assert run("prompt_join_list", prompts=["a", "b", "c"], separator=", ")[0] == "a, b, c"

    def test_empty(self):
        assert run("prompt_join_list", prompts=[], separator=", ")[0] == ""

    def test_custom_separator(self):
        assert run("prompt_join_list", prompts=["a", "b"], separator=" | ")[0] == "a | b"
