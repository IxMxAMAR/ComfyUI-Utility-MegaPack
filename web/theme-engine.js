import { invalidateCache } from "./cache.js";

const STATIC_KEYS = ["bgcolor", "color", "boxcolor", "titlecolor", "titletext", "shape"];

// Stripe drawn on the left edge of each node when the theme declares
// `categoryAccents`. Width is in node-local pixels.
const ACCENT_STRIPE_WIDTH = 4;


export class ThemeEngine {
  #originals = new WeakMap();

  constructor({ themeApi } = {}) {
    this.themeApi = themeApi ?? { motionAllowed: () => true };
  }

  applyTheme(node, theme) {
    this.#restoreOriginals(node);
    invalidateCache(node);

    if (!theme || theme.id === "default") return;

    this.#snapshotOriginals(node);

    if (theme.staticConfig) {
      for (const key of STATIC_KEYS) {
        if (theme.staticConfig[key] !== undefined) {
          node[key] = theme.staticConfig[key];
        }
      }
    }

    const accent = theme.categoryAccents ? resolveCategoryAccent(node, theme.categoryAccents) : null;
    const origFg = node.onDrawForeground;

    // Wrap onDrawForeground if EITHER the theme draws a foreground or we have
    // a category-accent stripe to add. Combining both into one wrap keeps the
    // hook count minimal — important because LiteGraph calls these every frame.
    if (theme.drawForeground || accent) {
      node.onDrawForeground = function (ctx) {
        if (origFg) origFg.call(this, ctx);
        if (accent) {
          const h = this.size?.[1] ?? 0;
          if (h > 0) {
            ctx.save();
            ctx.fillStyle = accent;
            ctx.fillRect(0, 0, ACCENT_STRIPE_WIDTH, h);
            ctx.restore();
          }
        }
        if (theme.drawForeground) {
          theme.drawForeground.call(this, ctx, this, theme.themeApi);
        }
      };
    }

    const origBg = node.onDrawBackground;
    if (theme.drawBackground) {
      node.onDrawBackground = function (ctx) {
        if (origBg) origBg.call(this, ctx);
        theme.drawBackground.call(this, ctx, this, theme.themeApi);
      };
    }

    if (node.setDirtyCanvas) node.setDirtyCanvas(true, true);
  }

  #snapshotOriginals(node) {
    if (this.#originals.has(node)) return;
    const snap = {
      onDrawForeground: node.onDrawForeground,
      onDrawBackground: node.onDrawBackground,
    };
    for (const key of STATIC_KEYS) snap[key] = node[key];
    this.#originals.set(node, snap);
  }

  #restoreOriginals(node) {
    const snap = this.#originals.get(node);
    if (!snap) return;
    for (const key of STATIC_KEYS) node[key] = snap[key];
    node.onDrawForeground = snap.onDrawForeground;
    node.onDrawBackground = snap.onDrawBackground;
    this.#originals.delete(node);
    if (node.setDirtyCanvas) node.setDirtyCanvas(true, true);
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
 * These are GLOBAL (one per graph) so they live outside ThemeEngine's
 * per-node WeakMap. Originals are stashed in module state and restored on
 * the next theme application.
 */
let _originalGroupColors = null;
let _originalCanvasBg = null;

export function applyGlobalTweaks(app, theme) {
  if (!app) return;

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

  // ----- Group colors
  if (!app.graph?._groups) return;
  if (theme?.groupColors) {
    if (_originalGroupColors === null) {
      _originalGroupColors = app.graph._groups.map((g) => ({ g, color: g.color, bgcolor: g.bgcolor }));
    }
    for (const grp of app.graph._groups) {
      if (theme.groupColors.color) grp.color = theme.groupColors.color;
      if (theme.groupColors.bgcolor) grp.bgcolor = theme.groupColors.bgcolor;
    }
    app.canvas?.setDirty?.(true, true);
  } else if (_originalGroupColors !== null) {
    for (const { g, color, bgcolor } of _originalGroupColors) {
      g.color = color;
      g.bgcolor = bgcolor;
    }
    _originalGroupColors = null;
    app.canvas?.setDirty?.(true, true);
  }
}
