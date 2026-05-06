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
  drawForeground(ctx, node, themeApi) {
    const w = node.size?.[0] ?? 0;
    const h = node.size?.[1] ?? 0;
    if (w <= 0 || h <= 0) return;
    ctx.save();
    ctx.strokeStyle = "#00f0ff";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(w - 12, 0);
    ctx.lineTo(w, 12);
    ctx.stroke();

    if (themeApi && themeApi.motionAllowed("low")) {
      ctx.shadowColor = "rgba(255,45,146,0.4)";
      ctx.shadowBlur = 12;
      ctx.strokeStyle = "#ff2d92";
      ctx.lineWidth = 1;
      ctx.strokeRect(0, 0, w, h);
    }
    ctx.restore();
  },
  themeApiVersion: 1,
};
