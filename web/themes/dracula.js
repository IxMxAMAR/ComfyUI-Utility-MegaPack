export default {
  id: "dracula",
  displayName: "Dracula",
  motion: "low",
  staticConfig: {
    bgcolor: "#282a36",
    color: "#bd93f9",
    titlecolor: "#bd93f9",
    titletext: "#282a36",
    boxcolor: "#8be9fd",
  },
  wirePalette: {
    default: "#bd93f9",
    IMAGE: "#8be9fd",       // cyan
    LATENT: "#bd93f9",      // purple
    MASK: "#f8f8f2",        // foreground
    CONDITIONING: "#f1fa8c", // yellow
    MODEL: "#ff79c6",       // pink
    CLIP: "#ffb86c",        // orange
  },
  categoryAccents: {
    image: "#8be9fd",
    latent: "#bd93f9",
    conditioning: "#f1fa8c",
    sampling: "#50fa7b",
    loaders: "#ffb86c",
    default: "#ff79c6",
  },
  groupColors: { color: "#bd93f9", bgcolor: "#21222c" },
  bgGridColor: "#1e1f29",
  // Soft purple outline via two strokes — replaces the previous ctx.shadowBlur
  // approach which became unusable under globalOverrideEnabled in v0.1.2.
  drawForeground(ctx, node, themeApi) {
    if (!themeApi || !themeApi.motionAllowed("low")) return;
    const w = node.size?.[0] ?? 0;
    const h = node.size?.[1] ?? 0;
    if (w <= 0 || h <= 0) return;
    ctx.save();
    // Wide outer halo, low alpha
    ctx.strokeStyle = "#bd93f9";
    ctx.globalAlpha = 0.25;
    ctx.lineWidth = 3;
    ctx.strokeRect(0.5, 0.5, w - 1, h - 1);
    // Thin core line
    ctx.globalAlpha = 0.7;
    ctx.lineWidth = 1;
    ctx.strokeRect(0.5, 0.5, w - 1, h - 1);
    ctx.restore();
  },
  themeApiVersion: 1,
};
