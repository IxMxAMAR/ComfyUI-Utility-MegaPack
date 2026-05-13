/**
 * Wire (link/connection) theming.
 *
 * Three concerns:
 *   1. Per-data-type color palette: mutate ComfyUI's `app.canvas.default_connection_color_byType`
 *      when a theme has a `wirePalette`. Save originals so we can restore.
 *   2. Render mode (bezier/straight/linear/manhattan): set `app.canvas.links_render_mode` directly.
 *   3. Thickness/opacity: wrap `LGraphCanvas.prototype.renderLink` once, read live settings.
 *
 * We deliberately do NOT add an idle animation loop (would force per-frame
 * `setDirty` calls and drain battery). ComfyUI's native execution-flow dots
 * are preserved via the wrap calling the original `renderLink`.
 *
 * Verified against existing packs:
 *   - ComfyUI-Custom-Scripts mutates `app.canvas.links_render_mode`.
 *   - ComfyUI-KJNodes mutates `default_connection_color_byType` and wraps `renderLink`.
 */

let _originalColorByType = null;
let _renderLinkPatched = false;
let _wireState = {
  // Live values read by the wrapped renderLink on every call.
  // Mutate these when settings change; no need to re-wrap.
  thickness: 1.0,        // multiplier on ctx.lineWidth (1.0 = LiteGraph default)
  opacity: 1.0,          // ctx.globalAlpha multiplier
  forcedColor: null,     // if set, override the per-type color
};


export function applyWirePalette(app, palette) {
  if (!app?.canvas) return;
  if (!_originalColorByType) {
    // Snapshot the original color map ONCE so we can restore later.
    _originalColorByType = { ...(app.canvas.default_connection_color_byType || {}) };
  }
  if (!palette) {
    // Restore originals
    if (_originalColorByType) {
      app.canvas.default_connection_color_byType = { ..._originalColorByType };
    }
    _wireState.forcedColor = null;
    return;
  }
  // Apply theme palette. Unknown types keep the original color.
  app.canvas.default_connection_color_byType = {
    ..._originalColorByType,
    ...palette,
  };
  _wireState.forcedColor = palette.default ?? null;
}


/**
 * Set the link render mode globally.
 *   1 = Straight, 2 = Linear, 3 = Spline/Bezier, 4 = L-Shape (ComfyUI Manhattan).
 *   null = leave ComfyUI's user setting alone.
 */
export function applyWireRenderMode(app, mode) {
  if (!app?.canvas) return;
  if (mode !== null && mode !== undefined) {
    app.canvas.links_render_mode = Number(mode);
    app.canvas.setDirty?.(true, true);
  }
}


export function setWireThickness(multiplier) {
  _wireState.thickness = Number(multiplier) || 1.0;
}


export function setWireOpacity(alpha) {
  _wireState.opacity = Math.max(0, Math.min(1, Number(alpha) || 1.0));
}


/**
 * Install a one-time wrapper around LGraphCanvas.prototype.renderLink that
 * applies the live thickness/opacity settings. Safe against repeated calls.
 */
export function ensureRenderLinkWrapped(LGraphCanvas) {
  if (_renderLinkPatched || !LGraphCanvas?.prototype?.renderLink) return;
  const original = LGraphCanvas.prototype.renderLink;
  LGraphCanvas.prototype.renderLink = function (ctx, a, b, link, skip_border, flow, color, start_dir, end_dir, num_sublines) {
    // Fast path: no theme changes
    if (_wireState.thickness === 1.0 && _wireState.opacity === 1.0) {
      return original.call(this, ctx, a, b, link, skip_border, flow, color, start_dir, end_dir, num_sublines);
    }
    ctx.save();
    if (_wireState.thickness !== 1.0) {
      // Multiply lineWidth before original draws. LiteGraph reads ctx.lineWidth
      // when it calls stroke(), so this scales the wire.
      ctx.lineWidth = (ctx.lineWidth || 2) * _wireState.thickness;
    }
    if (_wireState.opacity !== 1.0) {
      ctx.globalAlpha = (ctx.globalAlpha ?? 1) * _wireState.opacity;
    }
    const result = original.call(this, ctx, a, b, link, skip_border, flow, color, start_dir, end_dir, num_sublines);
    ctx.restore();
    return result;
  };
  _renderLinkPatched = true;
}


/** For tests only. */
export function _resetForTests() {
  _originalColorByType = null;
  _renderLinkPatched = false;
  _wireState = { thickness: 1.0, opacity: 1.0, forcedColor: null };
}
