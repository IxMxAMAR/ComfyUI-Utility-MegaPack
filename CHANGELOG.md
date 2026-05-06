# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] — 2026-05-06

Initial alpha. 156 operations across 7 functional nodes plus a smoke-test node, 11 themes, full Python + JS test suites.

### Added — Foundation
- Package scaffold (`pyproject.toml`, MIT license, requirements pin).
- `MegaPackNodeBase` with `OpRegistry` and `@op` decorator pattern (O(1) dispatch).
- `AnyType` wildcard via the standard string-subclass trick.
- Output padding helper with type-appropriate defaults; opaque types (`MODEL`/`CLIP`/`VAE`) pad to `None` so ComfyUI runtime can fail-fast at wire-time.
- `THEME_CHOICES` constant feeding the per-node theme dropdown (13 entries: 11 themes + 2 placeholders).
- `SmokeTestNode` with one `echo` op for registration verification.
- GitHub Actions CI matrix on Python 3.10/3.11/3.12.

### Added — Theme system
- 11 themes: Cyberpunk, Minimalist, Glassmorphic, Retro Terminal, Default, Holographic, Paper / Ink, Brutalist, Solarized Dark, Dracula, High-Contrast.
- `ThemeRegistry`, `ThemeEngine` (idempotent apply via `WeakMap` originals snapshot), `themeApi` (motion gates), `resolveTheme` cascade (per-node → pack default → ComfyUI-wide override).
- 6 sidebar settings under `megapack.*` (pack default, global override, global theme, respect-existing-custom-drawing, reduce-motion, heavy-theme node budget).
- Vitest + jsdom test infrastructure, 26 JS tests.

### Added — Programming node (60 ops)
- Encoding (5): base64 encode/decode, URL encode/decode, slug.
- Logic & Bits (8): boolean and/or/not/xor, bitwise and/or/xor/shift.
- Math & Signals (10): math add/subtract/multiply/divide/clamp/lerp, stats mean/median/std, random uniform.
- Text & Parsing (12): regex match/extract/replace/split, Jinja2 template render, string concat/upper/lower/trim, tokenize words, YAML parse/dump.
- Data Structures (10): dict get/set/keys/values/merge, list length/index/slice/sort/reverse.
- Control Flow (7): for_loop, while_loop (sandboxed), if_else, compare, eval_expr (sandboxed), null_coalesce, switch_case.
- Crypto (8): SHA-256 / SHA-512 / MD5 / BLAKE2b, HMAC sign + verify (constant-time), AES-256-GCM encrypt + decrypt with HKDF key derivation.

### Added — Prompt node (9 ops)
- Batch pick (multi-line + index), file loader, wildcard expander, weighted mixer, Jinja template render, cleaner with optional dedupe, negative auto-build (4 presets), token counter (CLIP-style heuristic), join list.

### Added — Image Pro node (27 ops)
- Loaders: path, glob (newest), random-from-folder, last-saved, sequence-Nth.
- Value & Color: invert, HSL shift, levels (black/white/gamma), posterize, solarize, threshold-binary.
- Spatial: pixelate, gaussian blur, unsharp sharpen, chromatic aberration, vignette, lens distortion, tile repeat.
- Style: gaussian noise, film grain, JPEG quality degrade, glitch (horizontal strips), halftone dots.
- Inspect: image_info (w/h/channels/mean/range), channel ops (swap/isolate/grayscale), palette extract (top-N via PIL adaptive quantization), 32-bin histogram.

### Added — Mask & Latent node (10 ops)
- Mask from color (with tolerance), erode, dilate, gaussian blur, combine (union/intersect/diff/xor), inspect (coverage/bbox/centroid).
- Latent inspect (shape/dtype/range), math (add/subtract/blend), noise inject, smart upscale (auto-pick bilinear vs bicubic).

### Added — IO & Workflow node (21 ops)
- Filesystem: mkdir, exists, glob, copy, move, delete (refuses directories).
- Path: join, basename, dirname, sanitize-filename.
- Network: HTTP GET / POST with 30s default timeout, 50MB cap, status code always returned.
- Workflow: filename format (`{date}_{seed}_{prompt_slug}.png` tokens), save image with manifest sidecar, notify (webhook + console), workflow stop / assert, sweep parameter range, watch folder for next file.
- System: stats (RAM/disk/GPU info via psutil + torch.cuda when available).

### Added — Convenience node (14 ops)
- Universal reroute, multi-output split (1→5), switch (5-way), gate (conditional pass), counter (per-key), timer (start + elapsed), debug print, pin selector, preset save / load (JSON bundle), side-by-side compare (concatenates IMAGE pairs with auto height-pad), workflow note (annotated passthrough), value select (5-string switch).

### Added — Models & Sampling node (14 ops)
- Read .safetensors metadata header (no model load).
- Model fingerprint (SHA-256 of first 1MB).
- List installed models in folder (extension-filtered).
- LoRA trigger-word extractor.
- Aspect ratio picker (8 presets) with long-side scaling.
- SDXL bucket picker (9 official training resolutions).
- Snap to multiple (e.g. round to nearest 64).
- Megapixel calculator (target MP + ratio → snapped W,H).
- Seed cycle (fixed / increment / decrement / random / from-string SHA-256).
- Multi-seed batch.
- Seed history (last 32 seeds emitted).
- Sampler picker, scheduler picker.
- Sampler params bundle (sampler+scheduler+steps+cfg+denoise as one DICT).

### Security
- `simpleeval` for all expression evaluation; `__` substring rejected.
- `cryptography` library for all crypto; AES-GCM only; HMAC `compare_digest`.
- HTTP capped at 50MB response, 30s timeout, max 5 redirects.
- Filesystem `fs_delete` refuses directories.
- Preset names with path separators rejected.
