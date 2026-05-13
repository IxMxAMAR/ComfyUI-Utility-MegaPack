// Synthwave: 80s retro-futurism. Neon pink-to-purple header gradient,
// cyan accent. Distinguished from Cyberpunk by hot horizontal gradients
// rather than corner clips + glow.
const HEADER_STOPS = ["#ff007f", "#7900ff"];

export default {
  id: "synthwave",
  displayName: "Synthwave",
  motion: "low",
  staticConfig: {
    bgcolor: "#120424",
    color: "#1a0533",
    titlecolor: "#1a0533",
    titletext: "#ffffff",
    boxcolor: "#00f0ff",
  },
  wirePalette: {
    default: "#ff007f",
    IMAGE: "#ff61dc",
    LATENT: "#bf5af2",
    MASK: "#00f0ff",
    CONDITIONING: "#ffea00",
    MODEL: "#ff5e5e",
  },
  categoryAccents: {
    image: "#ff61dc",
    latent: "#bf5af2",
    conditioning: "#ffea00",
    sampling: "#00f0ff",
    default: "#ff007f",
  },
  groupColors: { color: "#ff007f", bgcolor: "#1a0533" },
  bgGridColor: "#08011a",
  drawForeground(ctx, node, themeApi) {
    const w = node.size?.[0] ?? 0;
    const h = node.size?.[1] ?? 0;
    if (w <= 0 || h <= 0) return;
    ctx.save();
    // Pink-to-purple horizontal gradient stripe at the very top, 3px tall.
    // Mimics a synthwave sunset bar without the cost of a full header repaint.
    const grad = ctx.createLinearGradient(0, 0, w, 0);
    grad.addColorStop(0, HEADER_STOPS[0]);
    grad.addColorStop(1, HEADER_STOPS[1]);
    ctx.fillStyle = grad;
    ctx.fillRect(0, -3, w, 3);
    if (themeApi && themeApi.motionAllowed("low")) {
      // Subtle cyan neon outline (no shadowBlur — uses two-pass strokes).
      ctx.strokeStyle = "#00f0ff";
      ctx.globalAlpha = 0.25;
      ctx.lineWidth = 3;
      ctx.strokeRect(0.5, 0.5, w - 1, h - 1);
      ctx.globalAlpha = 0.8;
      ctx.lineWidth = 1;
      ctx.strokeRect(0.5, 0.5, w - 1, h - 1);
    }
    ctx.restore();
  },
  themeApiVersion: 2,
};
