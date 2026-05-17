export default {
  id: "glassmorphic",
  displayName: "Glassmorphic",
  motion: "low",
  staticConfig: {
    bgcolor: "#3c2890",
    color: "#2c1f70",
    titlecolor: "#2c1f70",
    titletext: "#ffffff",
    boxcolor: "#c084fc",
  },
  wirePalette: {
    default: "#c084fc",
    IMAGE: "#a78bfa",
    LATENT: "#c084fc",
    MASK: "#ffffff",
    CONDITIONING: "#fbbf24",
    MODEL: "#f472b6",
  },
  categoryAccents: {
    image: "#a78bfa",
    latent: "#c084fc",
    conditioning: "#fbbf24",
    default: "#c084fc",
  },
  groupColors: { color: "#c084fc", bgcolor: "#241b66" },
  bgGridColor: "#1b1356",
  drawForeground(ctx, node, themeApi) {
    if (!themeApi || !themeApi.motionAllowed("low")) return;
    const w = node.size?.[0] ?? 0;
    const h = node.size?.[1] ?? 0;
    if (w <= 0 || h <= 0) return;
    ctx.save();
    // The glass highlight gradient depends only on the strip height (capped
    // at 28), not the node width. Cache by that height.
    const stripH = Math.min(28, h);
    let cached = node._mp_glass_grad;
    if (!cached || cached.h !== stripH) {
      const grad = ctx.createLinearGradient(0, 0, 0, stripH);
      grad.addColorStop(0, "rgba(255,255,255,0.12)");
      grad.addColorStop(1, "rgba(255,255,255,0)");
      cached = node._mp_glass_grad = { h: stripH, grad };
    }
    ctx.fillStyle = cached.grad;
    ctx.fillRect(0, 0, w, stripH);
    ctx.restore();
  },
  themeApiVersion: 1,
};
