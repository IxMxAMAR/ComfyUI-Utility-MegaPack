"""Smoke tests for v0.3.0 new ops + regression tests for the bug fixes."""
import os
import sys

import pytest
import torch

_HERE = os.path.dirname(os.path.abspath(__file__))
_PKG_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))
if _PKG_ROOT not in sys.path:
    sys.path.insert(0, _PKG_ROOT)


# ---------------- json_path ----------------

class TestJsonPath:
    def setup_method(self):
        from mp_nodes.programming.operations.data_struct import json_path
        self.fn = json_path

    def test_dotted_key_lookup(self):
        text, _, raw = self.fn(None, {"user": {"name": "Alice"}}, "user.name")
        assert raw == "Alice"
        assert text == "Alice"

    def test_list_index(self):
        _, _, raw = self.fn(None, {"items": [10, 20, 30]}, "items[1]")
        assert raw == 20

    def test_negative_index(self):
        _, _, raw = self.fn(None, {"results": [{"url": "a"}, {"url": "b"}]}, "results[-1].url")
        assert raw == "b"

    def test_missing_key_returns_default(self):
        text, _, _ = self.fn(None, {"a": 1}, "b.c.d", default_on_miss="fallback")
        assert text == "fallback"


# ---------------- Latent dict preservation (regression for HIGH-5) ----------------

class TestLatentDictPreservation:
    def test_latent_math_preserves_noise_mask(self):
        from mp_nodes.mask_latent.operations.latent_ops import latent_math
        noise_mask = torch.ones(1, 1, 8, 8)
        a = {"samples": torch.randn(1, 4, 8, 8), "noise_mask": noise_mask, "batch_index": [0]}
        b = {"samples": torch.randn(1, 4, 8, 8)}
        result = latent_math(None, a, b, math_op="add")[0]
        assert "noise_mask" in result, "noise_mask was silently dropped!"
        assert "batch_index" in result
        assert torch.equal(result["noise_mask"], noise_mask)

    def test_latent_noise_inject_preserves_aux(self):
        from mp_nodes.mask_latent.operations.latent_ops import latent_noise_inject
        latent = {"samples": torch.zeros(1, 4, 4, 4), "noise_mask": torch.ones(1, 1, 4, 4)}
        result = latent_noise_inject(None, latent, strength=0.1, seed=42)[0]
        assert "noise_mask" in result


# ---------------- latent_nan_guard ----------------

class TestLatentNanGuard:
    def test_raises_on_nan(self):
        from mp_nodes.mask_latent.operations.latent_ops import latent_nan_guard
        bad = {"samples": torch.tensor([[[[float("nan")]]]])}
        with pytest.raises(RuntimeError, match="NaN"):
            latent_nan_guard(None, bad, on_nan="raise")

    def test_zero_out_replaces_nan(self):
        from mp_nodes.mask_latent.operations.latent_ops import latent_nan_guard
        bad = {"samples": torch.tensor([[[[float("nan"), 1.0]]]])}
        cleaned, info = latent_nan_guard(None, bad, on_nan="zero_out")
        assert torch.isnan(cleaned["samples"]).sum().item() == 0
        assert info["nan_count"] == 1

    def test_clean_latent_passes_through(self):
        from mp_nodes.mask_latent.operations.latent_ops import latent_nan_guard
        good = {"samples": torch.randn(1, 4, 4, 4)}
        out, info = latent_nan_guard(None, good, on_nan="raise")
        assert info["nan_count"] == 0
        assert out is good


# ---------------- latent_pad_crop ----------------

class TestLatentPadCrop:
    def test_pad_larger(self):
        from mp_nodes.mask_latent.operations.latent_ops import latent_pad_crop
        s = torch.ones(1, 4, 8, 8)
        out = latent_pad_crop(None, {"samples": s}, target_h=16, target_w=16, fill_value=0.0)[0]
        assert out["samples"].shape == (1, 4, 16, 16)
        # Center should still be the original 1.0; edges should be 0.0.
        assert out["samples"][0, 0, 0, 0].item() == 0.0
        assert out["samples"][0, 0, 8, 8].item() == 1.0

    def test_crop_smaller(self):
        from mp_nodes.mask_latent.operations.latent_ops import latent_pad_crop
        s = torch.randn(1, 4, 16, 16)
        out = latent_pad_crop(None, {"samples": s}, target_h=8, target_w=8)[0]
        assert out["samples"].shape == (1, 4, 8, 8)


# ---------------- Alpha preservation (regression for HIGH-6) ----------------

class TestAlphaPreservation:
    def test_invert_preserves_alpha(self):
        from mp_nodes.image_pro.operations.value_ops import invert
        rgba = torch.cat([torch.zeros(1, 4, 4, 3), torch.full((1, 4, 4, 1), 0.7)], dim=-1)
        out = invert(None, rgba)[0]
        assert out.shape == rgba.shape
        # Alpha unchanged.
        assert torch.allclose(out[..., 3], torch.full((1, 4, 4), 0.7))
        # RGB inverted.
        assert torch.allclose(out[..., :3], torch.ones(1, 4, 4, 3))

    def test_threshold_binary_preserves_alpha(self):
        from mp_nodes.image_pro.operations.value_ops import threshold_binary
        rgba = torch.cat([
            torch.full((1, 4, 4, 3), 0.7),
            torch.full((1, 4, 4, 1), 0.3),
        ], dim=-1)
        out = threshold_binary(None, rgba, threshold=0.5)[0]
        assert out.shape == rgba.shape
        assert torch.allclose(out[..., 3], torch.full((1, 4, 4), 0.3))


# ---------------- Mask kernel parity (regression for HIGH-7) ----------------

class TestMaskKernelParity:
    def test_even_kernel_preserves_shape(self):
        from mp_nodes.mask_latent.operations.mask_ops import mask_erode, mask_dilate
        m = torch.ones(1, 16, 16)
        out_e = mask_erode(None, m, kernel_size=4)[0]
        out_d = mask_dilate(None, m, kernel_size=4)[0]
        assert out_e.shape == m.shape, f"erode shape mismatch: {out_e.shape} vs {m.shape}"
        assert out_d.shape == m.shape, f"dilate shape mismatch: {out_d.shape} vs {m.shape}"


# ---------------- aspect_ratio_pick /8 snap (regression for HIGH-8) ----------------

class TestAspectRatioSnap:
    def test_snaps_height_to_multiple_of_8(self):
        from mp_nodes.models_sampling.operations.resolution import aspect_ratio_pick
        # 1000 / 16 * 9 = 562.5 → would have been 562 (not /8). Should snap to 560.
        w, h, info = aspect_ratio_pick(None, "16:9", long_side=1000)
        assert w % 8 == 0
        assert h % 8 == 0


# ---------------- mask_from_depth ----------------

class TestMaskFromDepth:
    def test_threshold_range(self):
        from mp_nodes.mask_latent.operations.mask_ops import mask_from_depth
        img = torch.full((1, 4, 4, 3), 0.6)
        mask = mask_from_depth(None, img, min_value=0.4, max_value=0.8)[0]
        assert (mask == 1.0).all()

    def test_outside_range_is_zero(self):
        from mp_nodes.mask_latent.operations.mask_ops import mask_from_depth
        img = torch.full((1, 4, 4, 3), 0.9)
        mask = mask_from_depth(None, img, min_value=0.0, max_value=0.5)[0]
        assert (mask == 0.0).all()


# ---------------- pad_to_multiple ----------------

class TestPadToMultiple:
    def test_pads_to_multiple(self):
        from mp_nodes.image_pro.operations.spatial_ops import pad_to_multiple
        img = torch.ones(1, 70, 130, 3)
        out, w, h = pad_to_multiple(None, img, multiple=64, fill_value=0.0)
        assert w == 192
        assert h == 128
        # Original region preserved.
        assert (out[:, :70, :130, :] == 1.0).all()
        # Padded region filled.
        assert (out[:, 70:, :, :] == 0.0).all()

    def test_already_aligned_passthrough(self):
        from mp_nodes.image_pro.operations.spatial_ops import pad_to_multiple
        img = torch.randn(1, 64, 64, 3)
        out, w, h = pad_to_multiple(None, img, multiple=64)
        assert out is img
        assert (w, h) == (64, 64)


# ---------------- image_composite_over ----------------

class TestImageComposite:
    def test_normal_blend_with_alpha(self):
        from mp_nodes.image_pro.operations.value_ops import image_composite_over
        bg = torch.zeros(1, 4, 4, 3)
        fg = torch.cat([torch.ones(1, 4, 4, 3), torch.ones(1, 4, 4, 1)], dim=-1)
        out = image_composite_over(None, bg, fg, blend_mode="normal", opacity=0.5)[0]
        # Fully opaque alpha, opacity=0.5 → result should be 0.5 everywhere.
        assert torch.allclose(out, torch.full((1, 4, 4, 3), 0.5), atol=1e-5)


# ---------------- halftone_dots perf (regression for CRITICAL-4) ----------------

class TestHalftonePerf:
    def test_completes_on_512x512_quickly(self):
        """v0.2.x would freeze for many seconds; we just verify it returns."""
        import time
        from mp_nodes.image_pro.operations.style_ops import halftone_dots
        img = torch.rand(1, 512, 512, 3)
        t0 = time.monotonic()
        out = halftone_dots(None, img, dot_size=6)[0]
        elapsed = time.monotonic() - t0
        assert out.shape == img.shape
        # Should complete in well under 5 seconds on any reasonable machine.
        assert elapsed < 5.0, f"halftone_dots took {elapsed:.1f}s — regression!"
