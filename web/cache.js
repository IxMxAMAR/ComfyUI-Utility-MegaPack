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
  const key = `${themeId}:${width}x${height}`;
  if (!node._mp_pattern_cache) node._mp_pattern_cache = {};
  let entry = node._mp_pattern_cache[key];
  if (entry) return entry;

  const w = Math.ceil(width);
  const h = Math.ceil(height);
  const canvas = HAS_OFFSCREEN ? new OffscreenCanvas(w, h) : Object.assign(document.createElement("canvas"), { width: w, height: h });
  const ctx = canvas.getContext("2d");
  render(ctx, w, h);

  // Cap cache size per node to avoid unbounded growth when nodes resize a lot.
  const entries = Object.keys(node._mp_pattern_cache);
  if (entries.length > 4) {
    // Drop the oldest (first inserted) entry. Map insertion order is fine.
    delete node._mp_pattern_cache[entries[0]];
  }
  node._mp_pattern_cache[key] = canvas;
  return canvas;
}


/**
 * Invalidate a node's pattern cache. Call when a theme changes or when the
 * node is going to be re-themed.
 */
export function invalidateCache(node) {
  if (node) delete node._mp_pattern_cache;
}
