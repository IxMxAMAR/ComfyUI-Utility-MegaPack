# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.1] — 2026-05-17

Two user-reported bugs from v0.3.0:

- **Category accent stripe bled past collapsed nodes.** When a node was
  collapsed, LiteGraph kept `node.size[1]` at the un-collapsed value and did
  NOT clip per-node `onDrawForeground` to the collapsed title pill, so the
  left-edge accent stripe (and any theme `drawForeground`/`drawBackground`)
  painted a vertical bar into empty canvas below the pill. Now we skip all
  MegaPack theme decoration when `node.flags.collapsed` is true.
- **Wire render mode dropdown was off-by-one and contained a fictional
  option.** LiteGraph's actual constants are `HIDDEN=-1, STRAIGHT=0,
  LINEAR=1, SPLINE=2`. v0.3.0 mapped dropdown index → setting value 1:1,
  so picking "straight" actually set LINEAR, picking "linear" set SPLINE,
  and "bezier (spline)" / "manhattan (L-shape)" sent invalid values 3/4
  that LiteGraph ignored (silently falling back to default spline). The
  perceived behavior was "only Straight works" — because LINEAR lines look
  passably straight. The dropdown now has explicit label→value pairs,
  drops the non-existent Manhattan option, and adds Hidden. Options:
  off / hidden / straight / linear / spline (bezier).

## [0.3.0] — 2026-05-17

Big audit + fix release driven by two full-codebase Gemini Pro reviews
(Python backend + JS frontend) plus first-party verification of every
critical finding. Four security bugs, three memory leaks, eight correctness
bugs, ten new utility ops, and two new theme UX features.

### Security — fix immediately if you ever load shared workflows

- **Sandboxed Jinja2.** Both `template_render` (programming) and
  `prompt_template_render` (prompt) now use `SandboxedEnvironment`. The
  previous `Environment` allowed attribute-walk payloads like
  `{{ obj.__class__.__bases__[0].__subclasses__() }}` to pivot into
  arbitrary Python execution — RCE via any shared `.json` workflow.
- **Removed `~` from filesystem allow-list.** `fs_delete` / `fs_move` /
  `fs_copy` previously accepted any path under the user's home directory,
  letting a malicious workflow wipe `~/.ssh/id_rsa` or overwrite
  `~/.bashrc`. The allow-list is now strictly ComfyUI's input / output /
  temp roots. Override with `UTILITY_MEGAPACK_ALLOW_ARBITRARY_PATHS=1`.
- **`save_image_with_manifest` is confined.** Previously bypassed
  `_require_confined` entirely → arbitrary file write anywhere on disk.
  Filename is also basename-sanitized to reject `../` traversal.
- **SSRF block on HTTP nodes.** `http_get`, `http_post`, and
  `notify_webhook` now reject requests to loopback / RFC1918 / link-local
  hosts by default. Catches the AWS metadata endpoint (`169.254.169.254`)
  and prevents local-service pivots. Override with
  `UTILITY_MEGAPACK_ALLOW_INTERNAL_HTTP=1` if you genuinely need local
  Ollama / LM Studio access (the new `llm_enhance_prompt` op auto-respects
  this).
- **Case-insensitive path confinement on Windows.** `_path_is_confined`
  now `os.path.normcase`'s both sides so `c:\comfyui\input` matches a root
  registered as `C:\ComfyUI\input`.

### Fixed — Critical correctness / perf

- **O(N²) blowup in `halftone_dots`.** Inner loop allocated a full
  `np.ogrid[:h, :w]` per cell. 1024² with `dot_size=6` = ~30B ops and a
  multi-second worker freeze. Now operates on cell-local coords; ~1M ops.
- **Latent dict keys preserved.** `latent_math`, `latent_noise_inject`,
  and `latent_upscale_smart` previously returned `{"samples": out}`,
  silently dropping `noise_mask` (used for inpainting!) and `batch_index`.
  Now shallow-copy the input dict and swap samples.
- **Alpha channel preserved.** `invert` and `threshold_binary`
  destroyed transparency on RGBA inputs. Now split RGB / alpha and
  re-attach.
- **Mask erode/dilate kernel parity.** Even `kernel_size` produced
  asymmetric padding (`F.max_pool2d` returned `H+1, W+1`, crashing
  downstream). Now force odd.
- **`aspect_ratio_pick` snaps to /8.** Previously `long_side=1000` + 16:9
  produced `1000×562`, which crashed SD UNet/VAE. Now snapped to multiples
  of 8.

### Fixed — Theme engine (JS)

- **`window.matchMedia()` hoisted out of per-frame hot path.** Was being
  called inside `motionAllowed()` for every themed node every frame —
  ≈20k MQL allocations/sec at 200Hz × 100 themed nodes, collapsing canvas
  FPS from 200 to 25. Now evaluated once at construction, refreshed via
  `change` listener. **This is the fix users will feel most.**
- **Wrap-once theme engine.** v0.2.x snapshot-and-restored
  `onDrawForeground` on every theme change, which silently destroyed
  wrappers installed by OTHER extensions after us. v0.3 installs one
  wrapper per node and dispatches via `node._mp_theme`. Other extensions
  can wrap us freely on either side.
- **Memory leaks fixed.**
  - `themedNodes` Set is now cleaned on `nodeRemoved`. Previously deleted
    nodes lingered forever AND broke the `heavyThemeNodeBudget` check.
  - `_originalGroupColors` is now a `WeakMap` keyed on the group object,
    so deleted groups can be garbage collected.
- **Cache canvas reused across resizes.** Previously each new `WxH` allocated
  a fresh `OffscreenCanvas` (and re-ran e_ink's per-pixel loop!) every
  mouse-move frame during a node resize. Now resize in place.
- **Wire thickness uses `connections_width` properly.** Previously
  mutated `ctx.lineWidth` inside a `renderLink` wrap; LiteGraph overwrites
  `lineWidth` from `connections_width` in the original draw, so the wrap
  was effectively a no-op. Now scales `connections_width` directly.
- **New groups auto-themed.** `app.graph.onGroupAdded` is hooked so
  groups created while a global theme is active inherit the theme's
  group colors immediately.
- **Gradient caching** in `synthwave` and `glassmorphic` themes (per
  node + size). Eliminates per-frame `CanvasGradient` allocation.
- **Budget setting triggers redraw** — animations now start/stop
  immediately when `heavyThemeNodeBudget` changes.
- **Removed dead `forcedColor` field** in wire-engine — was assigned but
  never read.

### Added — New utility ops (10)

- **`json_path`** (Programming / Data Structures) — extract nested values
  via dotted path: `user.name`, `items[0].price`, `results[-1].url`.
- **`latent_nan_guard`** (Mask & Latent / Latent) — inspect a latent for
  NaN / Inf (common with SDXL FP16). `raise` stops the workflow before
  decode wastes GPU on a black image; `zero_out` / `clamp` recover.
- **`latent_pad_crop`** (Mask & Latent / Latent) — pad-with-fill or
  center-crop in latent space, no VAE roundtrip.
- **`mask_from_depth`** (Mask & Latent / Mask) — threshold a depth /
  normal / grayscale map into the `[min_value, max_value]` range. Pairs
  with MiDaS, ZoeDepth, etc.
- **`mask_invert`** (Mask & Latent / Mask) — 1.0 − mask.
- **`save_images_zip`** (IO & Workflow / Workflow) — pack a batch of
  IMAGEs into a single ZIP with a `manifest.json` sidecar. Great for
  sweeps and grid generation.
- **`color_match_histogram`** (Image Pro / Value & Color) — per-channel
  histogram CDF mapping to match a source's color distribution to a
  reference. Compositing must-have.
- **`image_composite_over`** (Image Pro / Value & Color) — alpha-aware
  composite with optional mask gate and add / multiply / screen blend
  modes. Auto-resizes foreground to match background.
- **`frequency_separation`** (Image Pro / Style) — split into hi-freq
  (detail / texture) or lo-freq (color / tone). Pro retouching primitive.
- **`pad_to_multiple`** (Image Pro / Spatial) — pad H × W up to the next
  multiple of N. SDXL likes /64; ControlNet preprocessors need /8.
- **`llm_enhance_prompt`** (Prompt) — expand a basic prompt via a local
  Ollama-compatible LLM endpoint (Ollama native or OpenAI-style fallback;
  LM Studio and llama.cpp server both work). Five style presets.

### Added — Theme UX

- **Right-click → "Theme…" submenu** on every node, including vanilla
  ComfyUI nodes that lack a `theme` widget. Toggle in settings.
- **Auto-contrast title text.** If a theme's `titletext` has WCAG <4.5
  contrast against its `titlecolor`, the engine flips it to pure black or
  white. Toggle in settings (default on).

### Deferred to v0.4

- `IS_CHANGED` for file/network ops (requires `_base.py` schema change)
- Theme presets save/load (settings panel already persists)
- Wire color sync from source node (needs per-link color override; risk
  of conflict with other extensions)
- Animated execution-flow wires (needs ComfyUI execution event hookup)

## [0.2.0] — 2026-05-06

Major feature release: wire/connection theming, 4 new themes, per-node-category accent stripes, offscreen-canvas pattern caching, and group/grid color sync. Scope informed by a second Gemini Pro code review.

### Added — Wires (connections / "spaghetti noodles")
- **Per-theme wire color palette.** Themes declare `wirePalette: { default, IMAGE, LATENT, MASK, ... }`. On apply, ComfyUI's `app.canvas.default_connection_color_byType` is mutated to match. Originals snapshotted and restored when the theme changes.
- **Wire render-mode dropdown.** New setting `Utility-MegaPack — Wire render mode` lets you choose straight / linear / bezier / manhattan globally. `0` (default) leaves ComfyUI's own setting alone.
- **Wire thickness multiplier.** New setting (default `1.0`) scales `ctx.lineWidth` on every link draw via a one-time `LGraphCanvas.prototype.renderLink` wrap. ComfyUI's native execution-flow dots are preserved (the wrap calls the original).
- **Wire opacity slider.** New setting (`0.0` – `1.0`) multiplies `ctx.globalAlpha`.

### Added — 4 new themes (15 total)
- **Blueprint** — cyanotype schematic, cached faint white grid overlay
- **Nord** — frosted arctic, muted aurora palette
- **Synthwave** — 80s retro-futurism, pink→purple header gradient + cyan neon outline (no `shadowBlur`)
- **E-Ink** — pure monochrome, sparse dithered noise overlay (cached)

### Added — Per-node-category accent stripes
- Themes can declare `categoryAccents: { image, latent, conditioning, sampling, loaders, default }`. The theme engine draws a 4-px colored stripe on the left edge of each node based on `node.constructor.category`. Matches the first path segment (case-insensitive), so `"image/upscaling"` and `"image"` both get the `image` accent.

### Added — Group color & canvas background sync
- Themes declare `groupColors: { color, bgcolor }` and `bgGridColor`. On apply, `app.graph._groups` are repainted and `app.canvas.clear_background_color` is set. Originals snapshotted and restored.

### Performance
- **OffscreenCanvas pattern cache** (`web/cache.js`). Static expensive draws — Retro Terminal scanlines, Blueprint grid, E-Ink noise — render once per `(themeId, width, height)` to an offscreen canvas and blit with a single `drawImage` thereafter. Per-node frame cost for these themes drops from O(node-area) to O(1).
- Wire-engine fast path: when `wireThickness === 1.0` and `wireOpacity === 1.0`, the wrap calls the original `renderLink` directly with zero extra `save`/`restore`.

### Theme schema bumped to v2
- Themes that declare any of `wirePalette` / `categoryAccents` / `groupColors` / `bgGridColor` should set `themeApiVersion: 2`. v1 themes still load — fields are simply not applied.

### Tests
- Python: **340 / 340** passing (was 340, plus an updated `test_total_count_is_seventeen` for the 15-theme list)
- JS: **33 / 33** passing (was 26, plus 7 new for `resolveCategoryAccent`)

## [0.1.3] — 2026-05-06

### Fixed — Performance
- **Canvas lag with global override + animated themes.** Cyberpunk and Dracula previously used `ctx.shadowBlur` (12–14 px Gaussian convolution per draw), which is one of the most expensive HTML canvas operations. With `globalOverrideEnabled = true`, every visible node drew a shadow-blurred rectangle every frame, dropping framerate to single digits on graphs with 20+ nodes. v0.1.3 replaces the shadow with a two-pass strokeRect (wide low-alpha outer line + thin core line) — visually nearly identical, ~100× cheaper.
- **`heavyThemeNodeBudget` default lowered from 60 → 25.** Even with the cheaper draw path, animated motion gets suppressed sooner on heavy graphs. Raise manually if your GPU is comfortable.

## [0.1.2] — 2026-05-06

This release fixes a critical loader bug from 0.1.1 plus 6 issues surfaced by an outside code review.

### Fixed — Critical loader collision
- **`'nodes' is not a package` at ComfyUI startup.** v0.1.1 attempted to fix the import error by injecting our package directory into `sys.path`, but ComfyUI's core ships its own `nodes.py` module. Since `sys.modules['nodes']` was already populated with ComfyUI's `nodes.py` (a single-file module), our absolute imports like `from nodes.smoke import ...` resolved to that module and failed because it has no `.smoke` attribute. **Fix:** renamed internal packages from `nodes/` → `mp_nodes/` and `shared/` → `mp_shared/` so our path injection cannot shadow ComfyUI core.

### Fixed — Security
- **`http_post` no longer reads unbounded responses into memory.** Previous version called `requests.post(...)` and checked `len(resp.content)` after the full body buffered. v0.1.2 streams with `iter_content` and enforces the 50 MB cap mid-stream, matching `http_get`. (DoS protection.)
- **AES key derivation switched from HKDF (no work factor) to PBKDF2-HMAC-SHA256 with 600,000 iterations and a random per-encryption salt.** Ciphertext format is now base64(salt[16] ‖ nonce[12] ‖ tag+ct). Old v0.1.x ciphertexts are not decryptable by 0.1.2+.
- **`fs_mkdir`, `fs_copy`, `fs_move`, `fs_delete` now reject paths outside the allow-list** (ComfyUI input/output/temp + user home). Override with `UTILITY_MEGAPACK_ALLOW_ARBITRARY_PATHS=1` if needed. Closes a host-wide read/write/delete vulnerability when ComfyUI is exposed over a network.

### Fixed — UX / correctness
- **Settings dropdowns** for "Pack default theme" and "Global theme" now declare `options` so ComfyUI renders the actual list instead of an empty combo.
- **LATENT default pad changed from a hardcoded (1, 4, 8, 8) zero tensor to `{}` empty dict.** SD3 / Flux use 16-channel latents; the old default caused cryptic shape mismatches downstream. Now downstream nodes see a clean missing-key error.
- **`@op` decorator now rejects widget names `mode` and `theme` at registration time.** These collided with framework kwargs and surfaced as cryptic runtime "multiple values for argument" errors only when the op was first invoked.
- **`_pad_outputs` docstring** updated to match the relaxed opaque-type behavior introduced in 0.1.1.

## [0.1.1] — 2026-05-06

### Fixed
- ComfyUI loader compatibility: inject the package directory into `sys.path` at import time so `from nodes._base import ...` and `from shared.conversions import ...` resolve under ComfyUI's `spec_from_file_location` loader. **(Insufficient — superseded by the package rename in 0.1.2; see above.)**

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
