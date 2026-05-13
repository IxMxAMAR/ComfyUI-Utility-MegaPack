"""Tests for the Data Structures category."""

import pytest

from mp_nodes.programming import ProgrammingNode


def run(mode, **kwargs):
    return ProgrammingNode().process(mode=mode, theme="(use pack default)", **kwargs)


class TestDict:
    def test_get_present_key(self):
        assert run("dict_get", data={"a": 1}, key="a", default="z")[6] == 1

    def test_get_missing_key_returns_default(self):
        assert run("dict_get", data={"a": 1}, key="b", default="fallback")[6] == "fallback"

    def test_set_returns_new_dict_does_not_mutate(self):
        original = {"a": 1}
        new = run("dict_set", data=original, key="b", value="2")[5]
        assert new == {"a": 1, "b": "2"}
        assert original == {"a": 1}

    def test_keys_sorted(self):
        assert run("dict_keys", data={"b": 1, "a": 2, "c": 3})[4] == ["a", "b", "c"]

    def test_values_in_key_sorted_order(self):
        assert run("dict_values", data={"b": 2, "a": 1, "c": 3})[4] == [1, 2, 3]

    def test_merge_b_wins_on_conflict(self):
        out = run("dict_merge", a={"x": 1, "y": 2}, b={"y": 99, "z": 3})[5]
        assert out == {"x": 1, "y": 99, "z": 3}


class TestList:
    def test_length(self):
        assert run("list_length", data=[1, 2, 3])[1] == 3

    def test_length_empty(self):
        assert run("list_length", data=[])[1] == 0

    def test_index_positive(self):
        assert run("list_index", data=[10, 20, 30], index=1)[6] == 20

    def test_index_negative(self):
        assert run("list_index", data=[10, 20, 30], index=-1)[6] == 30

    def test_index_empty_list_raises(self):
        with pytest.raises(RuntimeError):
            run("list_index", data=[], index=0)

    def test_slice(self):
        assert run("list_slice", data=[1, 2, 3, 4], start=1, stop=3)[4] == [2, 3]

    def test_slice_stop_zero_goes_to_end(self):
        assert run("list_slice", data=[1, 2, 3], start=1, stop=0)[4] == [2, 3]

    def test_sort_default(self):
        assert run("list_sort", data=["b", "a", "c"], reverse=False)[4] == ["a", "b", "c"]

    def test_sort_reverse(self):
        assert run("list_sort", data=["b", "a", "c"], reverse=True)[4] == ["c", "b", "a"]

    def test_sort_mixed_types_does_not_crash(self):
        # Sorts by str representation
        out = run("list_sort", data=[1, "b", 2, "a"], reverse=False)[4]
        assert len(out) == 4

    def test_reverse(self):
        assert run("list_reverse", data=[1, 2, 3])[4] == [3, 2, 1]
