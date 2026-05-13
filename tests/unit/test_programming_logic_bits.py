"""Tests for the Logic & Bits category."""

from mp_nodes.programming import ProgrammingNode


def run(mode, **kwargs):
    return ProgrammingNode().process(mode=mode, theme="(use pack default)", **kwargs)


def test_bool_and_truth_table():
    assert run("bool_and", a=True, b=True)[3] is True
    assert run("bool_and", a=True, b=False)[3] is False
    assert run("bool_and", a=False, b=False)[3] is False


def test_bool_or_truth_table():
    assert run("bool_or", a=False, b=False)[3] is False
    assert run("bool_or", a=True, b=False)[3] is True


def test_bool_not_inverts():
    assert run("bool_not", a=True)[3] is False
    assert run("bool_not", a=False)[3] is True


def test_bool_xor_truth_table():
    assert run("bool_xor", a=True, b=True)[3] is False
    assert run("bool_xor", a=True, b=False)[3] is True
    assert run("bool_xor", a=False, b=False)[3] is False


def test_bitwise_and():
    assert run("bitwise_and", a=0b1100, b=0b1010)[1] == 0b1000


def test_bitwise_or():
    assert run("bitwise_or", a=0b1100, b=0b1010)[1] == 0b1110


def test_bitwise_xor():
    assert run("bitwise_xor", a=0b1100, b=0b1010)[1] == 0b0110


def test_bitwise_shift_left():
    assert run("bitwise_shift", a=1, places=4)[1] == 16


def test_bitwise_shift_right():
    assert run("bitwise_shift", a=16, places=-2)[1] == 4


def test_bitwise_shift_zero_is_identity():
    assert run("bitwise_shift", a=42, places=0)[1] == 42
