const COLORS = ["#ff006e", "#ffbe0b", "#06ffa5", "#00b4d8", "#c77dff"];

export default {
  id: "holographic",
  displayName: "Holographic",
  motion: "high",
  staticConfig: {
    bgcolor: "#0d0820",
    color: "#1a1140",
    titlecolor: "#1a1140",
    titletext: "#ffffff",
    boxcolor: "#c77dff",
  },
  drawForeground(ctx, node, themeApi) {
    const w = node.size?.[0] ?? 0;
    const h = node.size?.[1] ?? 0;
    if (w <= 0 || h <= 0) return;
    const animate = themeApi && themeApi.motionAllowed("high");
    const t = animate ? (Date.now() / 4000) % 1 : 0;
    ctx.save();
    const grad = ctx.createLinearGradient(0, 0, w, 0);
    for (let i = 0; i < COLORS.length; i++) {
      const stop = ((i / COLORS.length) + t) % 1;
      grad.addColorStop(stop, COLORS[i]);
    }
    ctx.strokeStyle = grad;
    ctx.lineWidth = 2;
    ctx.strokeRect(1, 1, w - 2, h - 2);
    ctx.restore();
  },
  themeApiVersion: 1,
};
