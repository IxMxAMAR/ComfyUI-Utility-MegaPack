import { invalidateCache } from "./cache.js";

const STATIC_KEYS = ["bgcolor", "color", "boxcolor", "titlecolor", "titletext", "shape"];

// Stripe drawn on the left edge of each node when the theme declares
// `categoryAccents`. Width is in node-local pixels.
const ACCENT_STRIPE_WIDTH = 4;


/**
 * Wrap-once theme engine.
 *
 * v0.2.x snapshot-and-restored `onDrawForeground` on every theme change. If
 * ANOTHER extension wrapped the draw method AFTER us, the next theme switch
 * blindly restored our snapshot — silently destroying the other extension's
 * wrapper.
 *
 * v0.3.0 installs ONE wrapper per node on first apply, then stores the active
 * theme + accent on the node itself. Theme switches just update those fields;
 * we never touch `onDrawForeground` again. This means our wrapper survives
 * being re-wrapped by other extensions: their wrap calls ours, ours calls the
 * pre-MegaPack original.
 *
 * Static keys (bgcolor/color/etc.) ARE still snapshot/restored — those are
 * plain property assignments and aren't subject to the wrap-stomp problem.
 */
const MP_FG_TAG = "_mp_fg_wrapped";
const MP_BG_TAG = "_mp_bg_wrapped";
const MP_STATIC_SNAP = "_mp_static_snap";

export class ThemeEngine {
  constructor({ themeApi } = {}) {
    this.themeApi = themeApi ?? { motionAllowed: () => true };
  }

  applyTheme(node, theme, opts = {}) {
    invalidateCache(node);
    const isDefault = !theme || theme.id === "default";

    // Update the live state read by our (already-installed) wrappers.
    node._mp_theme = isDefault ? null : theme;
    node._mp_accent = (!isDefault && theme.categoryAccents)
      ? resolveCategoryAccent(node, theme.categoryAccents)
      : null;

    // Static-config keys: snapshot once, then restore-or-overwrite each apply.
    this.#restoreStatic(node);
    if (!isDefault && theme.staticConfig) {
      this.#snapshotStatic(node);
      for (const key of STATIC_KEYS) {
        if (theme.staticConfig[key] !== undefined) {
          node[key] = theme.staticConfig[key];
        }
      }
      // Auto-contrast: if the theme's titletext has poor contrast against the
      // titlecolor (often happens with user-customized themes), flip it to
      // pure black or white based on which gives better luminance contrast.
      if (opts.autoContrast && theme.staticConfig.titlecolor && theme.staticConfig.titletext) {
        const bgL = _relLuminance(theme.staticConfig.titlecolor);
        const fgL = _relLuminance(theme.staticConfig.titletext);
        const ratio = _contrastRatio(bgL, fgL);
        if (ratio < 4.5) {  // WCAG AA threshold
          node.titletext = bgL > 0.5 ? "#000000" : "#ffffff";
        }
      }
    }

    // Install draw wrappers exactly once per node, regardless of theme. Other
    // extensions can wrap us before or after and we both compose cleanly.
    //
    // Collapsed-node note: LiteGraph keeps `node.size` at the expanded values
    // even when `flags.collapsed` is true (the node renders as a small title
    // pill but the size array doesn't shrink). LiteGraph also does NOT clip
    // per-node `onDrawForeground` to the collapsed pill, so a naive accent
    // stripe at `node.size[1]` height bleeds past the bottom of the pill.
    // Skip our theme decoration entirely when collapsed; the title pill is
    // tiny and decorations there look broken anyway.
    if (!node[MP_FG_TAG]) {
      const origFg = node.onDrawForeground;
      node.onDrawForeground = function (ctx) {
        if (origFg) origFg.call(this, ctx);
        if (this.flags?.collapsed) return;
        const accent = this._mp_accent;
        if (accent) {
          const h = this.size?.[1] ?? 0;
          if (h > 0) {
            ctx.save();
            ctx.fillStyle = accent;
            ctx.fillRect(0, 0, ACCENT_STRIPE_WIDTH, h);
            ctx.restore();
          }
        }
        const t = this._mp_theme;
        if (t?.drawForeground) {
          t.drawForeground.call(this, ctx, this, t.themeApi);
        }
      };
      node[MP_FG_TAG] = true;
    }

    if (!node[MP_BG_TAG]) {
      const origBg = node.onDrawBackground;
      node.onDrawBackground = function (ctx) {
        if (origBg) origBg.call(this, ctx);
        if (this.flags?.collapsed) return;
        const t = this._mp_theme;
        if (t?.drawBackground) {
          t.drawBackground.call(this, ctx, this, t.themeApi);
        }
      };
      node[MP_BG_TAG] = true;
    }

    if (node.setDirtyCanvas) node.setDirtyCanvas(true, true);
  }

  #snapshotStatic(node) {
    if (node[MP_STATIC_SNAP]) return;
    const snap = {};
    for (const key of STATIC_KEYS) snap[key] = node[key];
    node[MP_STATIC_SNAP] = snap;
  }

  #restoreStatic(node) {
    const snap = node[MP_STATIC_SNAP];
    if (!snap) return;
    for (const key of STATIC_KEYS) node[key] = snap[key];
    delete node[MP_STATIC_SNAP];
  }
}


/**
 * Match a node's category against the theme's category-accent map.
 *
 * Categories are typically slash-delimited strings like "image/upscaling".
 * We match the first path segment so themes can declare just "image" once
 * and have it apply to "image", "image/upscaling", "image/postprocessing".
 *
 * Falls back to `accents.default` if no segment matches.
 */
export function resolveCategoryAccent(node, accents) {
  const raw = node?.constructor?.category ?? node?.category ?? "";
  if (!raw || typeof accents !== "object") return accents?.default ?? null;
  const segments = String(raw).toLowerCase().split("/").filter(Boolean);
  for (const seg of segments) {
    if (accents[seg]) return accents[seg];
  }
  return accents.default ?? null;
}


/**
 * Apply theme-level global tweaks: group colors + canvas background.
 *
 * Originals are stashed on the GROUP OBJECTS (via WeakMap-ish properties) so
 * deleted groups can be garbage collected. v0.2.x kept strong refs in a
 * module-level array, which leaked.
 */
let _originalCanvasBg = null;
const _groupOriginals = new WeakMap();

// Track which theme is currently driving the global tweaks. Lets newly
// created groups (via onGroupAdded in extension.js) pick up the theme.
let _activeGlobalTheme = null;
export function getActiveGlobalTheme() { return _activeGlobalTheme; }

export function applyGlobalTweaks(app, theme) {
  if (!app) return;
  _activeGlobalTheme = theme ?? null;

  // ----- Background grid color
  if (theme?.bgGridColor) {
    if (_originalCanvasBg === null) {
      _originalCanvasBg = app.canvas?.clear_background_color ?? null;
    }
    if (app.canvas) {
      app.canvas.clear_background_color = theme.bgGridColor;
      app.canvas.setDirty?.(true, true);
    }
  } else if (_originalCanvasBg !== null && app.canvas) {
    app.canvas.clear_background_color = _originalCanvasBg;
    _originalCanvasBg = null;
    app.canvas.setDirty?.(true, true);
  }

  // ----- Group colors (stashed on each group via WeakMap)
  if (!app.graph?._groups) return;
  if (theme?.groupColors) {
    for (const grp of app.graph._groups) {
      if (!_groupOriginals.has(grp)) {
        _groupOriginals.set(grp, { color: grp.color, bgcolor: grp.bgcolor });
      }
      if (theme.groupColors.color) grp.color = theme.groupColors.color;
      if (theme.groupColors.bgcolor) grp.bgcolor = theme.groupColors.bgcolor;
    }
    app.canvas?.setDirty?.(true, true);
  } else {
    let restored = false;
    for (const grp of app.graph._groups) {
      const orig = _groupOriginals.get(grp);
      if (!orig) continue;
      grp.color = orig.color;
      grp.bgcolor = orig.bgcolor;
      _groupOriginals.delete(grp);
      restored = true;
    }
    if (restored) app.canvas?.setDirty?.(true, true);
  }
}


// ---------------- Color helpers for auto-contrast ----------------

function _parseHex(c) {
  if (typeof c !== "string") return null;
  const m = /^#?([0-9a-f]{6})$/i.exec(c.trim());
  if (!m) {
    const m3 = /^#?([0-9a-f]{3})$/i.exec(c.trim());
    if (!m3) return null;
    const [r, g, b] = m3[1].split("").map((x) => parseInt(x + x, 16));
    return [r, g, b];
  }
  const v = parseInt(m[1], 16);
  return [(v >> 16) & 0xff, (v >> 8) & 0xff, v & 0xff];
}

function _relLuminance(color) {
  const rgb = _parseHex(color);
  if (!rgb) return 0.5;
  const [r, g, b] = rgb.map((c) => {
    const s = c / 255;
    return s <= 0.03928 ? s / 12.92 : Math.pow((s + 0.055) / 1.055, 2.4);
  });
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

function _contrastRatio(l1, l2) {
  const lighter = Math.max(l1, l2);
  const darker = Math.min(l1, l2);
  return (lighter + 0.05) / (darker + 0.05);
}


/** Apply the active theme's group colors to a freshly-added group. */
export function applyThemeToGroup(group) {
  const theme = _activeGlobalTheme;
  if (!theme?.groupColors || !group) return;
  if (!_groupOriginals.has(group)) {
    _groupOriginals.set(group, { color: group.color, bgcolor: group.bgcolor });
  }
  if (theme.groupColors.color) group.color = theme.groupColors.color;
  if (theme.groupColors.bgcolor) group.bgcolor = theme.groupColors.bgcolor;
}
