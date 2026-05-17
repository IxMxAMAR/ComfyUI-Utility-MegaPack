/**
 * Wire (link/connection) theming.
 *
 *   1. Per-data-type color palette: mutate `app.canvas.default_connection_color_byType`
 *      and store originals so we can restore on theme removal.
 *   2. Render mode (bezier/straight/linear/manhattan): set `app.canvas.links_render_mode`.
 *   3. Thickness: scale LiteGraph's native `connections_width` property. (v0.2.x
 *      tried to mutate `ctx.lineWidth` inside a renderLink wrap, but LiteGraph
 *      overwrites lineWidth from connections_width inside the original
 *      renderLink anyway, so the wrap was a no-op.)
 *   4. Opacity: wrap renderLink to scale globalAlpha. There is no native
 *      LiteGraph property for link opacity, so a wrap is necessary here.
 *
 * Verified against existing packs:
 *   - ComfyUI-Custom-Scripts mutates `links_render_mode`.
 *   - ComfyUI-KJNodes mutates `default_connection_color_byType` and wraps `renderLink`.
 */

let _originalColorByType = null;
let _originalConnectionsWidth = null;
let _renderLinkPatched = false;
let _wireState = {
  thickness: 1.0,        // multiplier on connections_width
  opacity: 1.0,          // ctx.globalAlpha multiplier (applied in wrap)
};


export function applyWirePalette(app, palette) {
  if (!app?.canvas) return;
  if (!_originalColorByType) {
    _originalColorByType = { ...(app.canvas.default_connection_color_byType || {}) };
  }
  if (!palette) {
    app.canvas.default_connection_color_byType = { ..._originalColorByType };
    return;
  }
  // Apply theme palette merged over originals — unknown link types keep
  // their original colors.
  app.canvas.default_connection_color_byType = {
    ..._originalColorByType,
    ...palette,
  };
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


/** Scale LiteGraph's native connections_width by `multiplier`. */
export function applyWireThickness(app, multiplier) {
  _wireState.thickness = Number(multiplier) || 1.0;
  if (!app?.canvas) return;
  if (_originalConnectionsWidth === null) {
    // LiteGraph defaults to 3 in modern builds; snapshot whatever is live.
    _originalConnectionsWidth = app.canvas.connections_width ?? 3;
  }
  app.canvas.connections_width = _originalConnectionsWidth * _wireState.thickness;
  app.canvas.setDirty?.(true, false);
}


export function setWireOpacity(alpha) {
  _wireState.opacity = Math.max(0, Math.min(1, Number(alpha) || 1.0));
}


/**
 * Install a one-time wrapper around LGraphCanvas.prototype.renderLink that
 * applies the live opacity setting. Thickness is handled by mutating
 * `connections_width` (see applyWireThickness) and does NOT require a wrap.
 */
export function ensureRenderLinkWrapped(LGraphCanvas) {
  if (_renderLinkPatched || !LGraphCanvas?.prototype?.renderLink) return;
  const original = LGraphCanvas.prototype.renderLink;
  LGraphCanvas.prototype.renderLink = function (...args) {
    if (_wireState.opacity === 1.0) {
      return original.apply(this, args);
    }
    const ctx = args[0];
    const prev = ctx.globalAlpha ?? 1;
    ctx.globalAlpha = prev * _wireState.opacity;
    const result = original.apply(this, args);
    ctx.globalAlpha = prev;
    return result;
  };
  _renderLinkPatched = true;
}


/** For tests only. */
export function _resetForTests() {
  _originalColorByType = null;
  _originalConnectionsWidth = null;
  _renderLinkPatched = false;
  _wireState = { thickness: 1.0, opacity: 1.0 };
}
