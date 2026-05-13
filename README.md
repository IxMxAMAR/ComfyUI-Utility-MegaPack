# ComfyUI-Utility-MegaPack

Comprehensive utility node pack for ComfyUI — **156 operations across 7 functional nodes** plus a smoke-test node, with **11 swappable visual themes** that can be applied per-node, pack-wide, or globally across every ComfyUI node.

**Status:** Alpha. Core feature-complete.

## Install

Drop this directory into `ComfyUI/custom_nodes/` and restart ComfyUI. Required Python deps:

```
numpy>=1.24,<3
Pillow>=10.0,<12
requests>=2.31,<3
simpleeval>=0.9,<2
Jinja2>=3.1,<4
PyYAML>=6.0,<7
cryptography>=42.0,<46
```

`pip install -e .` from the package root installs them.

## Nodes

All nodes appear under the `Utility-MegaPack/` menu in ComfyUI. Each node has a two-level `mode` dropdown so a single node can perform many related operations.

| Node | Ops | What it does |
|---|---:|---|
| **Programming** | 60 | Control flow (for/while/if), data structures (dict/list/set), text/parsing (regex/Jinja/YAML), math + stats, logic + bitwise, crypto (SHA/HMAC/AES-GCM), encoding (base64/url/slug). Sandboxed expression evaluator. |
| **Prompt** | 9 | Batcher, file loader (.txt/.csv), wildcard expander (`__color__`), weighted mixer, Jinja template render, cleaner (dedupe + comma normalize), negative auto-build, token counter. |
| **Image Pro** | 27 | Loaders (path/glob/random/last-saved/sequence). Value/color (invert, HSL shift, levels, posterize, solarize, threshold). Spatial (pixelate, blur, sharpen, chromatic aberration, vignette, lens distortion, tile). Style (noise, film grain, JPEG quality degrade, glitch, halftone). Inspect (image_info, channel ops, palette extract, histogram). |
| **Mask & Latent** | 10 | Mask from color (with tolerance). Erode / dilate / blur. Combine (union/intersect/diff/xor). Inspect (coverage, bbox, centroid). Latent inspect / math / noise inject / smart upscale. |
| **IO & Workflow** | 21 | Filesystem (mkdir/exists/glob/copy/move/delete). Path ops (join/basename/dirname/sanitize). HTTP GET / POST. Save image with manifest sidecar. Filename builder (`{date}_{seed}_{prompt_slug}.png`). Notify (webhook + console). Workflow stop / assert. Sweep parameter range. Watch folder. System stats (RAM/disk/GPU). |
| **Convenience** | 14 | Universal reroute, multi-output split (1→5), switch, gate, counter, timer, debug print, pin selector, preset save/load, side-by-side compare, workflow note, value select. |
| **Models & Sampling** | 14 | Read .safetensors metadata (no model load). Model fingerprint hash. List installed models in folder. LoRA trigger-word extractor. Aspect ratio picker (8 presets). SDXL bucket picker (9 official sizes). Snap to multiple. Megapixel calculator. Seed cycle (fixed/incr/decr/random/from-string). Multi-seed batch. Seed history. Sampler / scheduler pickers. Sampler params bundle. |

## Themes

Fifteen themes ship in the box. Each can be applied per-node via the `theme` widget at the bottom of every Utility-MegaPack node, or pack-wide / ComfyUI-wide via the sidebar settings.

| Theme | Look |
|---|---|
| `default` | Vanilla ComfyUI grey + small `MP` corner badge |
| `cyberpunk` | Magenta + cyan glow, angular clip-cuts, monospace |
| `minimalist` | Clean off-white body, dark header, single accent stripe |
| `glassmorphic` | Frosted purple, soft gradients, rounded corners |
| `retro_terminal` | Phosphor green on black, scanline overlay |
| `holographic` | Animated rainbow border (gated by reduce-motion) |
| `paper_ink` | Aged-paper beige, ink dots |
| `brutalist` | Concrete grey, hard shadows, all-caps |
| `solarized_dark` | Ethan Schoonover's dev colorscheme |
| `dracula` | Famous purple+pink+cyan dark theme with halo glow |
| `high_contrast` | Pure white/black + safety yellow, WCAG AAA-ready |
| `blueprint` | Cyanotype schematic, faint white grid overlay |
| `nord` | Frosted arctic, muted aurora palette |
| `synthwave` | 80s retro-futurism, pink→purple gradient + cyan neon |
| `e_ink` | Pure monochrome, sparse dithered noise overlay |

### Wires & customizations (v0.2.0)

- **Theme-synced wire colors.** Each theme can declare a per-data-type wire palette (e.g. Cyberpunk paints IMAGE wires cyan and LATENT wires purple). Mutated on `app.canvas.default_connection_color_byType` and restored when you switch themes.
- **Wire render mode.** Setting → choose between straight, linear, bezier, or manhattan routing globally.
- **Wire thickness + opacity.** Settings → multiplier on `ctx.lineWidth` and `ctx.globalAlpha`. ComfyUI's native execution-flow dots are preserved.
- **Per-node-category accent stripes.** 4-pixel colored bar on the left edge of each node, color picked from `node.constructor.category` (e.g. all `image/*` nodes get the theme's image accent, all `latent/*` get the latent accent).
- **Group colors + canvas background** track the active theme.

Settings under `megapack.*` in the ComfyUI sidebar:
- `packDefault` — theme used when a node's widget is `(use pack default)`
- `globalOverrideEnabled` — when on, theme ALL ComfyUI nodes (not just MegaPack)
- `globalTheme` — theme used for the global override
- `respectExistingCustomDrawing` — skip nodes from other extensions (rgthree, KJNodes, etc.) that already do their own drawing
- `reduceMotion` — disable animation for accessibility / performance
- `heavyThemeNodeBudget` — animations skip when more than N themed nodes are visible (default 25)
- `wireRenderMode` — straight / linear / bezier / manhattan
- `wireThickness` — multiplier on link line width
- `wireOpacity` — link alpha 0.0 – 1.0

## Resolution cascade

Most-specific wins:

1. **Per-node theme** — `node.properties.megapack_theme` set via the dropdown widget
2. **Pack default** — used when the node's widget is `(use pack default)`
3. **ComfyUI-wide override** — used when global override is on (and the node is non-MP, OR per-node says `(use ComfyUI default)`)

Theme application is **idempotent** — the engine snapshots originals in a `WeakMap` and restores them before applying the new theme, so switching themes 100× never stacks 100 wrappers.

## Security

Hard rules:

- **Eval / expressions**: `simpleeval` only. `__` substring is rejected. No bare `eval()`.
- **Crypto**: `cryptography` library only — AES-GCM (authenticated), HMAC compares with `compare_digest`. AES key derived via HKDF so any-length string keys work.
- **HTTP**: 30 s default timeout, 50 MB max response, ≤ 5 redirects, status code always returned.
- **Filesystem `fs_delete`**: refuses directories, requires explicit `missing_ok` for missing files.
- **Preset names**: rejected if they contain path separators.

## Tests

```
pytest                      # 334 Python tests
npm test                    # 26 JS tests (Vitest + jsdom)
```

CI (GitHub Actions) runs the Python suite on Python 3.10, 3.11, and 3.12 against ubuntu-latest.

## License

MIT. See [LICENSE](LICENSE).
