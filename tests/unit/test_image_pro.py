"""Tests for ImageProNode operations."""

import json
import os

import pytest
import torch
from PIL import Image

from nodes.image_pro import ImageProNode


def run(mode, **kwargs):
    return ImageProNode().process(mode=mode, theme="(use pack default)", **kwargs)


@pytest.fixture
def red_image():
    """1×4×4×3 tensor, all red."""
    img = torch.zeros((1, 4, 4, 3))
    img[..., 0] = 1.0
    return img


@pytest.fixture
def gradient_image():
    """1×8×8×3 tensor with horizontal gradient on R channel."""
    img = torch.zeros((1, 8, 8, 3))
    for x in range(8):
        img[0, :, x, 0] = x / 7.0
    return img


@pytest.fixture
def temp_image_file(tmp_path):
    pil = Image.new("RGB", (16, 12), color=(120, 60, 30))
    p = tmp_path / "test.png"
    pil.save(p)
    return str(p)


class TestLoaders:
    def test_load_image_path(self, temp_image_file):
        out = run("load_image_path", path=temp_image_file)
        assert out[0].shape == (1, 12, 16, 3)
        assert out[2] == 16  # width
        assert out[3] == 12  # height

    def test_load_image_path_missing_raises(self):
        with pytest.raises(RuntimeError, match="not found"):
            run("load_image_path", path="/no/such/file.png")

    def test_load_random_seeded(self, tmp_path):
        for i in range(5):
            Image.new("RGB", (8, 8), (i * 10, i * 10, i * 10)).save(tmp_path / f"{i}.png")
        a = run("load_image_random_from_folder", folder=str(tmp_path), seed=42)
        b = run("load_image_random_from_folder", folder=str(tmp_path), seed=42)
        assert torch.equal(a[0], b[0])

    def test_load_sequence_nth(self, tmp_path):
        for i in range(3):
            Image.new("RGB", (8, 8), (i * 50, 0, 0)).save(tmp_path / f"img_{i}.png")
        out = run("load_image_sequence_nth", folder=str(tmp_path), index=1)
        assert out[2] == 8 and out[3] == 8

    def test_load_glob_picks_newest(self, tmp_path):
        import time
        for i, name in enumerate(["a.png", "b.png", "c.png"]):
            Image.new("RGB", (8, 8), (i * 80, 0, 0)).save(tmp_path / name)
            time.sleep(0.02)
        out = run("load_image_glob", pattern=f"{tmp_path}/*.png")
        assert out[0].shape == (1, 8, 8, 3)


class TestValueOps:
    def test_invert(self, red_image):
        out = run("invert", image=red_image)[0]
        assert out[0, 0, 0, 0].item() == 0.0  # R inverted
        assert out[0, 0, 0, 1].item() == 1.0  # G inverted from 0

    def test_hsl_hue_shift_changes_color(self, red_image):
        out = run("color_shift_hsl", image=red_image, hue_shift=0.33, saturation=1.0, lightness=1.0)[0]
        # Hue shift moves red → green-ish
        assert out[0, 0, 0, 1].item() > 0.5

    def test_levels_clamps_range(self, gradient_image):
        out = run("levels", image=gradient_image, black_point=0.5, white_point=1.0, gamma=1.0)[0]
        # Pixels below 0.5 clamp to 0
        assert out[0, 0, 0, 0].item() == 0.0
        assert out[0, 0, -1, 0].item() == pytest.approx(1.0, abs=0.01)

    def test_posterize_reduces_unique_values(self, gradient_image):
        out = run("posterize", image=gradient_image, bits=2)[0]
        unique_vals = torch.unique(out[..., 0])
        assert len(unique_vals) <= 4

    def test_solarize_inverts_above_threshold(self, gradient_image):
        out = run("solarize", image=gradient_image, threshold=0.5)[0]
        # Pixels originally near 1.0 should now be near 0
        assert out[0, 0, -1, 0].item() < 0.3

    def test_threshold_binary(self, gradient_image):
        out = run("threshold_binary", image=gradient_image, threshold=0.5)[0]
        assert torch.all((out == 0.0) | (out == 1.0))


class TestSpatialOps:
    def test_pixelate_changes_pixels(self, gradient_image):
        out = run("pixelate", image=gradient_image, block_size=4)[0]
        # Pixels in same 4×4 block should be equal
        assert torch.allclose(out[0, 0, 0], out[0, 0, 3])

    def test_blur_softens(self, gradient_image):
        out = run("blur_gaussian", image=gradient_image, radius=2.0)[0]
        # Variance after blur should be lower than before
        assert out.var() < gradient_image.var()

    def test_sharpen_runs(self, gradient_image):
        out = run("sharpen_unsharp", image=gradient_image, radius=1.0, amount=100, threshold=0)[0]
        assert out.shape == gradient_image.shape

    def test_chromatic_aberration_zero_is_identity(self, red_image):
        out = run("chromatic_aberration", image=red_image, shift_pixels=0)[0]
        assert torch.equal(out, red_image)

    def test_chromatic_aberration_shifts(self, gradient_image):
        out = run("chromatic_aberration", image=gradient_image, shift_pixels=2)[0]
        # The R channel should now differ from the original
        assert not torch.equal(out[..., 0], gradient_image[..., 0])

    def test_vignette_darkens_corners(self, red_image):
        # Make a 16×16 red image so corners are visible
        img = torch.zeros((1, 16, 16, 3))
        img[..., 0] = 1.0
        out = run("vignette", image=img, strength=0.8, softness=0.5)[0]
        # Corner darker than center
        assert out[0, 0, 0, 0].item() < out[0, 8, 8, 0].item()

    def test_lens_distortion_runs(self, gradient_image):
        out = run("lens_distortion", image=gradient_image, k=0.3)[0]
        assert out.shape == gradient_image.shape

    def test_tile_repeat(self, red_image):
        out = run("tile_repeat", image=red_image, cols=2, rows=2)[0]
        assert out.shape == (1, 8, 8, 3)


class TestStyleOps:
    def test_noise_seeded(self, red_image):
        a = run("noise_add", image=red_image, amount=0.1, seed=7)[0]
        b = run("noise_add", image=red_image, amount=0.1, seed=7)[0]
        assert torch.equal(a, b)

    def test_film_grain_seeded(self, gradient_image):
        a = run("film_grain", image=gradient_image, amount=0.1, seed=7)[0]
        b = run("film_grain", image=gradient_image, amount=0.1, seed=7)[0]
        assert torch.equal(a, b)

    def test_jpeg_quality_degrade(self, gradient_image):
        out = run("quality_degrade_jpeg", image=gradient_image, quality=20)[0]
        assert out.shape == gradient_image.shape
        # JPEG round-trip is lossy
        assert not torch.equal(out, gradient_image)

    def test_glitch_seeded(self, gradient_image):
        a = run("glitch_shift", image=gradient_image, strips=4, max_shift=2, seed=7)[0]
        b = run("glitch_shift", image=gradient_image, strips=4, max_shift=2, seed=7)[0]
        assert torch.equal(a, b)

    def test_halftone_runs(self, gradient_image):
        out = run("halftone_dots", image=gradient_image, dot_size=4)[0]
        assert out.shape == gradient_image.shape


class TestInspect:
    def test_image_info(self, gradient_image):
        out = run("image_info", image=gradient_image)
        assert out[2] == 8  # width
        assert out[3] == 8  # height
        info = json.loads(out[4])
        assert info["channels"] == 3
        assert info["batch"] == 1

    def test_channel_op_grayscale(self, red_image):
        out = run("channel_op", image=red_image, channel_action="grayscale")[0]
        # All 3 channels should be equal after grayscale
        assert torch.allclose(out[..., 0], out[..., 1])

    def test_channel_op_isolate_r(self, gradient_image):
        out = run("channel_op", image=gradient_image, channel_action="isolate_r")[0]
        # G and B should be zero
        assert torch.all(out[..., 1] == 0)
        assert torch.all(out[..., 2] == 0)

    def test_palette_extract(self, gradient_image):
        out = run("palette_extract", image=gradient_image, n_colors=4)[4]
        palette = json.loads(out)
        assert isinstance(palette, list)
        assert len(palette) <= 4
        assert all(len(c) == 3 for c in palette)

    def test_histogram(self, gradient_image):
        out = run("histogram_json", image=gradient_image)[4]
        hist = json.loads(out)
        assert "r" in hist and "g" in hist and "b" in hist
        assert len(hist["r"]) == 32
