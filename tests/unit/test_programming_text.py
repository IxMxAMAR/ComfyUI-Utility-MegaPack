"""Tests for the Text & Parsing category."""

import pytest

from nodes.programming import ProgrammingNode


def run(mode, **kwargs):
    return ProgrammingNode().process(mode=mode, theme="(use pack default)", **kwargs)


class TestRegex:
    def test_match_true(self):
        assert run("regex_match", text="hello world", pattern=r"world")[3] is True

    def test_match_false(self):
        assert run("regex_match", text="hello", pattern=r"world")[3] is False

    def test_extract_no_match_returns_empty(self):
        assert run("regex_extract", text="abc", pattern=r"\d+")[0] == ""

    def test_extract_default_group_zero(self):
        assert run("regex_extract", text="abc123def", pattern=r"\d+")[0] == "123"

    def test_extract_named_group(self):
        out = run("regex_extract", text="rev1.2.3", pattern=r"(\d+)\.(\d+)\.(\d+)", group=2)[0]
        assert out == "2"

    def test_extract_out_of_range_group(self):
        # group 5 doesn't exist
        assert run("regex_extract", text="abc", pattern=r"a(b)c", group=5)[0] == ""

    def test_replace(self):
        assert run("regex_replace", text="foo bar foo", pattern=r"foo", replacement="baz")[0] == "baz bar baz"

    def test_split_default_whitespace(self):
        assert run("regex_split", text="a b  c", pattern=r"\s+")[4] == ["a", "b", "c"]

    def test_split_max_splits(self):
        out = run("regex_split", text="a,b,c,d", pattern=",", max_splits=2)[4]
        assert out == ["a", "b", "c,d"]


class TestTemplate:
    def test_basic_render(self):
        out = run("template_render", template="hello {{name}}", vars_json='{"name": "world"}')[0]
        assert out == "hello world"

    def test_loops(self):
        out = run(
            "template_render",
            template="{% for x in items %}{{x}},{% endfor %}",
            vars_json='{"items": [1, 2, 3]}',
        )[0]
        assert out == "1,2,3,"

    def test_strict_undefined_raises(self):
        with pytest.raises(RuntimeError):
            run("template_render", template="{{nope}}", vars_json="{}")

    def test_invalid_vars_json_raises(self):
        with pytest.raises(RuntimeError):
            run("template_render", template="x", vars_json="not json")


class TestStringOps:
    def test_concat(self):
        assert run("string_concat", a="foo", b="bar", sep="-")[0] == "foo-bar"

    def test_concat_no_sep(self):
        assert run("string_concat", a="foo", b="bar", sep="")[0] == "foobar"

    def test_upper(self):
        assert run("string_upper", text="hello")[0] == "HELLO"

    def test_lower(self):
        assert run("string_lower", text="HELLO")[0] == "hello"

    def test_trim(self):
        assert run("string_trim", text="  hi  ")[0] == "hi"

    def test_tokenize_words(self):
        assert run("tokenize_words", text="hello   world  foo")[4] == ["hello", "world", "foo"]


class TestYAML:
    def test_parse_dict(self):
        out = run("yaml_parse", text="a: 1\nb: 2\n")[5]
        assert out == {"a": 1, "b": 2}

    def test_parse_empty(self):
        assert run("yaml_parse", text="")[5] == {}

    def test_parse_scalar_wraps_under_value(self):
        assert run("yaml_parse", text="42")[5] == {"value": 42}

    def test_dump(self):
        out = run("yaml_dump", data_json='{"a": 1}')[0]
        assert "a: 1" in out

    def test_dump_round_trip(self):
        original = {"alpha": 1, "beta": [1, 2, 3]}
        import json
        dumped = run("yaml_dump", data_json=json.dumps(original))[0]
        parsed = run("yaml_parse", text=dumped)[5]
        assert parsed == original
