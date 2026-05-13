"""Tests for THEME_CHOICES — the dropdown values for the per-node theme widget."""

from mp_nodes._base import THEME_CHOICES


def test_theme_choices_is_list_of_strings():
    assert isinstance(THEME_CHOICES, list)
    assert all(isinstance(c, str) for c in THEME_CHOICES)


def test_first_two_entries_are_pack_and_comfyui_defaults():
    assert THEME_CHOICES[0] == "(use pack default)"
    assert THEME_CHOICES[1] == "(use ComfyUI default)"


def test_all_eleven_themes_present():
    expected = {
        "cyberpunk", "minimalist", "glassmorphic", "retro_terminal",
        "default", "holographic", "paper_ink", "brutalist",
        "solarized_dark", "dracula", "high_contrast",
    }
    assert expected.issubset(set(THEME_CHOICES))


def test_total_count_is_thirteen():
    """Two placeholders + eleven themes = thirteen entries."""
    assert len(THEME_CHOICES) == 13


def test_no_duplicates():
    assert len(THEME_CHOICES) == len(set(THEME_CHOICES))
