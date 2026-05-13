export default {
  id: "cyberpunk",
  displayName: "Cyberpunk",
  motion: "low",
  staticConfig: {
    bgcolor: "#0a0612",
    color: "#1a0a2a",
    titlecolor: "#1a0a2a",
    titletext: "#00f0ff",
    boxcolor: "#ff2d92",
  },
  wirePalette: {
    default: "#ff2d92",
    IMAGE: "#00f0ff",
    LATENT: "#c084fc",
    MASK: "#ffffff",
    CONDITIONING: "#ffea00",
    MODEL: "#ff5e5e",
  },
  categoryAccents: {
    image: "#00f0ff",
    latent: "#c084fc",
    conditioning: "#ffea00",
    default: "#ff2d92",
  },
  groupColors: { color: "#ff2d92", bgcolor: "#1a0a2a" },
  bgGridColor: "#080411",
  // Cheap "fake glow" using two strokes with global alpha instead of
  // ctx.shadowBlur. shadowBlur is one of the most expensive canvas ops
  // (forces an offscreen Gaussian convolution per draw) and ate ~50ms/frame
  // when applied to every node under globalOverrideEnabled in v0.1.2.
  // Two strokeRects with no shadow are ~100x cheaper and look nearly identical.
  drawForeground(ctx, node, themeApi) {
    const w = node.size?.[0] ?? 0;
    const h = node.size?.[1] ?? 0;
    if (w <= 0 || h <= 0) return;
    ctx.save();

    // Cyan corner notch — always drawn (very cheap)
    ctx.strokeStyle = "#00f0ff";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(w - 12, 0);
    ctx.lineTo(w, 12);
    ctx.stroke();

    if (themeApi && themeApi.motionAllowed("low")) {
      // Outer halo: wide line, low alpha
      ctx.strokeStyle = "#ff2d92";
      ctx.globalAlpha = 0.25;
      ctx.lineWidth = 3;
      ctx.strokeRect(0.5, 0.5, w - 1, h - 1);
      // Core line: 1px, full alpha
      ctx.globalAlpha = 1;
      ctx.lineWidth = 1;
      ctx.strokeRect(0.5, 0.5, w - 1, h - 1);
    }
    ctx.restore();
  },
  themeApiVersion: 1,
};
