"""Tests for MaskLatentNode."""

import pytest
import torch

from nodes.mask_latent import MaskLatentNode


def run(mode, **kwargs):
    return MaskLatentNode().process(mode=mode, theme="(use pack default)", **kwargs)


@pytest.fixture
def red_image():
    img = torch.zeros((1, 8, 8, 3))
    img[..., 0] = 1.0  # all red
    return img


@pytest.fixture
def half_red_image():
    """Left half red, right half blue."""
    img = torch.zeros((1, 8, 8, 3))
    img[..., 0:4, 0] = 1.0
    img[..., 4:8, 2] = 1.0
    return img


@pytest.fixture
def small_mask():
    """1×8×8 mask with a 4×4 white square in the top-left."""
    m = torch.zeros((1, 8, 8))
    m[0, :4, :4] = 1.0
    return m


@pytest.fixture
def latent_a():
    return {"samples": torch.ones((1, 4, 8, 8))}


@pytest.fixture
def latent_b():
    return {"samples": torch.zeros((1, 4, 8, 8))}


class TestMaskOps:
    def test_from_color_red_match(self, red_image):
        mask = run("mask_from_color", image=red_image, r=1.0, g=0.0, b=0.0, tolerance=0.01)[0]
        assert mask.shape == (1, 8, 8)
        assert torch.all(mask == 1.0)

    def test_from_color_no_match(self, red_image):
        mask = run("mask_from_color", image=red_image, r=0.0, g=1.0, b=0.0, tolerance=0.01)[0]
        assert torch.all(mask == 0.0)

    def test_from_color_half(self, half_red_image):
        mask = run("mask_from_color", image=half_red_image, r=1.0, g=0.0, b=0.0, tolerance=0.01)[0]
        assert mask[0, 0, 0].item() == 1.0  # left side red
        assert mask[0, 0, 5].item() == 0.0  # right side blue

    def test_erode_shrinks(self, small_mask):
        out = run("mask_erode", mask=small_mask, kernel_size=3)[0]
        # Erosion shrinks the white square
        assert out.sum().item() < small_mask.sum().item()

    def test_dilate_grows(self, small_mask):
        out = run("mask_dilate", mask=small_mask, kernel_size=3)[0]
        assert out.sum().item() > small_mask.sum().item()

    def test_blur_softens(self, small_mask):
        out = run("mask_blur", mask=small_mask, radius=2.0)[0]
        # Blur produces non-binary values
        assert (out > 0.0).any() and (out < 1.0).any()

    def test_combine_union(self, small_mask):
        b = torch.zeros_like(small_mask)
        b[0, 4:, 4:] = 1.0
        out = run("mask_combine", a=small_mask, b=b, combine_op="union")[0]
        assert out.sum().item() == 32  # 16 + 16

    def test_combine_intersect(self, small_mask):
        b = torch.zeros_like(small_mask)
        b[0, 2:6, 2:6] = 1.0
        out = run("mask_combine", a=small_mask, b=b, combine_op="intersect")[0]
        # 2×2 overlap region
        assert out.sum().item() == 4

    def test_combine_diff(self, small_mask):
        b = torch.zeros_like(small_mask)
        b[0, 2:6, 2:6] = 1.0
        out = run("mask_combine", a=small_mask, b=b, combine_op="diff")[0]
        # small_mask minus their overlap
        assert out.sum().item() == 12

    def test_inspect_full_mask(self, small_mask):
        info = run("mask_inspect", mask=small_mask)[2]
        assert info["coverage_pct"] == 25.0
        assert info["bbox"] == [0, 0, 3, 3]
        assert info["centroid"][0] == pytest.approx(1.5, abs=0.01)


class TestLatentOps:
    def test_inspect(self, latent_a):
        info = run("latent_inspect", latent=latent_a)[2]
        assert info["shape"] == [1, 4, 8, 8]
        assert info["mean"] == 1.0

    def test_math_add(self, latent_a, latent_b):
        out = run("latent_math", a=latent_a, b=latent_b, math_op="add", weight=0.5)[1]
        assert torch.all(out["samples"] == 1.0)

    def test_math_blend_full_b(self, latent_a, latent_b):
        out = run("latent_math", a=latent_a, b=latent_b, math_op="blend", weight=1.0)[1]
        assert torch.all(out["samples"] == 0.0)

    def test_math_blend_half(self, latent_a, latent_b):
        out = run("latent_math", a=latent_a, b=latent_b, math_op="blend", weight=0.5)[1]
        assert torch.all(out["samples"] == 0.5)

    def test_math_subtract(self, latent_a, latent_b):
        out = run("latent_math", a=latent_a, b=latent_b, math_op="subtract", weight=0.5)[1]
        assert torch.all(out["samples"] == 1.0)

    def test_math_shape_mismatch_raises(self, latent_a):
        bad = {"samples": torch.zeros((1, 4, 16, 16))}
        with pytest.raises(RuntimeError, match="shape mismatch"):
            run("latent_math", a=latent_a, b=bad, math_op="add", weight=0.0)

    def test_noise_inject_seeded(self, latent_a):
        a = run("latent_noise_inject", latent=latent_a, strength=0.1, seed=7)[1]
        b = run("latent_noise_inject", latent=latent_a, strength=0.1, seed=7)[1]
        assert torch.equal(a["samples"], b["samples"])

    def test_upscale_smart_2x_bilinear(self, latent_a):
        out = run("latent_upscale_smart", latent=latent_a, scale=2.0)[1]
        assert out["samples"].shape == (1, 4, 16, 16)

    def test_upscale_smart_4x_bicubic(self, latent_a):
        out = run("latent_upscale_smart", latent=latent_a, scale=4.0)[1]
        assert out["samples"].shape == (1, 4, 32, 32)
