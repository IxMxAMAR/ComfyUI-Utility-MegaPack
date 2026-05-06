"""Tests for the Encoding category of ProgrammingNode."""

import pytest

from nodes.programming import ProgrammingNode


def run(mode, **kwargs):
    return ProgrammingNode().process(mode=mode, theme="(use pack default)", **kwargs)


class TestBase64:
    def test_encode_round_trip(self):
        encoded = run("base64_encode", text="hello world")[0]
        assert encoded == "aGVsbG8gd29ybGQ="

    def test_decode_round_trip(self):
        decoded = run("base64_decode", text="aGVsbG8gd29ybGQ=")[0]
        assert decoded == "hello world"

    def test_decode_invalid_raises(self):
        with pytest.raises(RuntimeError, match=r"\[ProgrammingNode/base64_decode\]"):
            run("base64_decode", text="not-base64!@#$")

    def test_encode_unicode(self):
        out = run("base64_encode", text="café")[0]
        assert run("base64_decode", text=out)[0] == "café"


class TestUrlEncode:
    def test_url_encode_quotes_reserved(self):
        out = run("url_encode", text="hello world & friends")[0]
        assert out == "hello%20world%20%26%20friends"

    def test_url_decode_handles_plus_as_space(self):
        out = run("url_decode", text="hello+world%26friends")[0]
        assert out == "hello world&friends"

    def test_url_round_trip(self):
        original = "a b/c?d=1&e=2"
        encoded = run("url_encode", text=original)[0]
        decoded = run("url_decode", text=encoded)[0]
        assert decoded == original


class TestSlug:
    def test_basic_slug(self):
        assert run("slug", text="Hello, World!")[0] == "hello-world"

    def test_strips_leading_trailing_hyphens(self):
        assert run("slug", text="!!! Hello !!!")[0] == "hello"

    def test_max_length_truncates(self):
        assert run("slug", text="a" * 200, max_length=10)[0] == "a" * 10

    def test_max_length_does_not_leave_trailing_hyphen(self):
        # 'foo-bar-baz' truncated to 4 would be 'foo-' but we strip trailing hyphens
        out = run("slug", text="foo bar baz", max_length=4)[0]
        assert not out.endswith("-")

    def test_unicode_collapses_to_hyphens(self):
        # Non-ASCII letters are not in [a-z0-9], so they collapse to hyphens
        out = run("slug", text="café-bistro")[0]
        # 'café-bistro' -> 'caf-bistro' (the é + - both collapse)
        assert out == "caf-bistro"
