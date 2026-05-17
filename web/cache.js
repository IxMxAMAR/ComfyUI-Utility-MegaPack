/**
 * OffscreenCanvas cache for expensive static draws.
 *
 * Use case: a theme draws the same complex pattern (scanlines, hatch, grid,
 * dither) inside every node's onDrawForeground every frame. Each individual
 * draw is fast, but at 60 FPS × 20 nodes × N strokes, the cost compounds.
 * Render once to an OffscreenCanvas keyed by (theme-id, width, height), then
 * blit with a single drawImage call on subsequent frames.
 *
 * Cache is attached to the node (`node._mp_pattern_cache`) so it dies with
 * the node and doesn't leak across graph reloads.
 */

const HAS_OFFSCREEN = typeof OffscreenCanvas !== "undefined";


/**
 * Get-or-render a cached pattern for this node.
 *
 * Cache is keyed by (node, themeId) — only ONE canvas per (node, themeId)
 * exists at a time. On size change we resize the existing canvas in place and
 * re-render rather than allocating a fresh one, which used to thrash the GC
 * (and re-run e_ink's per-pixel loop) on every mouse-move during a node
 * resize.
 *
 * @param {Object} node       The LiteGraph node.
 * @param {String} themeId    Used as the cache key namespace.
 * @param {Number} width      Pattern width (typically node.size[0]).
 * @param {Number} height     Pattern height (typically node.size[1]).
 * @param {Function} render   Callback `(ctx, width, height) => void` that draws
 *                            the pattern onto the provided context.
 * @returns The OffscreenCanvas (or HTMLCanvasElement fallback) ready to blit.
 *          Pass it to your main ctx via `ctx.drawImage(canvas, 0, 0)`.
 */
export function cachedPattern(node, themeId, width, height, render) {
  if (width <= 0 || height <= 0) return null;
  const w = Math.ceil(width);
  const h = Math.ceil(height);
  if (!node._mp_pattern_cache) node._mp_pattern_cache = {};
  let entry = node._mp_pattern_cache[themeId];

  if (entry && entry.w === w && entry.h === h) {
    return entry.canvas;
  }

  let canvas;
  if (entry) {
    // Reuse the existing canvas — resizing is faster than allocating.
    canvas = entry.canvas;
    canvas.width = w;
    canvas.height = h;
  } else {
    canvas = HAS_OFFSCREEN
      ? new OffscreenCanvas(w, h)
      : Object.assign(document.createElement("canvas"), { width: w, height: h });
  }

  const ctx = canvas.getContext("2d");
  // Setting width/height clears the canvas implicitly; just render.
  render(ctx, w, h);

  node._mp_pattern_cache[themeId] = { canvas, w, h };
  return canvas;
}


/**
 * Invalidate a node's pattern cache. Call when a theme changes or when the
 * node is going to be re-themed.
 */
export function invalidateCache(node) {
  if (node) delete node._mp_pattern_cache;
}
