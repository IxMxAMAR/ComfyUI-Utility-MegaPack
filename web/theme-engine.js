const STATIC_KEYS = ["bgcolor", "color", "boxcolor", "titlecolor", "titletext", "shape"];

export class ThemeEngine {
  #originals = new WeakMap();

  constructor({ themeApi } = {}) {
    this.themeApi = themeApi ?? { motionAllowed: () => true };
  }

  applyTheme(node, theme) {
    this.#restoreOriginals(node);

    if (!theme || theme.id === "default") return;

    this.#snapshotOriginals(node);

    if (theme.staticConfig) {
      for (const key of STATIC_KEYS) {
        if (theme.staticConfig[key] !== undefined) {
          node[key] = theme.staticConfig[key];
        }
      }
    }

    const origFg = node.onDrawForeground;
    if (theme.drawForeground) {
      node.onDrawForeground = function (ctx) {
        if (origFg) origFg.call(this, ctx);
        theme.drawForeground.call(this, ctx, this, theme.themeApi);
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
