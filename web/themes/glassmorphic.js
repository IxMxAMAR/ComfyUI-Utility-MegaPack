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
  drawForeground(ctx, node, themeApi) {
    if (!themeApi || !themeApi.motionAllowed("low")) return;
    const w = node.size?.[0] ?? 0;
    const h = node.size?.[1] ?? 0;
    if (w <= 0 || h <= 0) return;
    ctx.save();
    const grad = ctx.createLinearGradient(0, 0, 0, h);
    grad.addColorStop(0, "rgba(255,255,255,0.12)");
    grad.addColorStop(1, "rgba(255,255,255,0)");
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, w, Math.min(28, h));
    ctx.restore();
  },
  themeApiVersion: 1,
};
