export default {
  id: "retro_terminal",
  displayName: "Retro Terminal",
  motion: "none",
  staticConfig: {
    bgcolor: "#0a1a0a",
    color: "#2dff52",
    titlecolor: "#2dff52",
    titletext: "#0a1a0a",
    boxcolor: "#2dff52",
  },
  drawForeground(ctx, node) {
    const w = node.size?.[0] ?? 0;
    const h = node.size?.[1] ?? 0;
    if (w <= 0 || h <= 0) return;
    ctx.save();
    ctx.globalAlpha = 0.04;
    ctx.fillStyle = "#2dff52";
    for (let y = 0; y < h; y += 3) ctx.fillRect(0, y, w, 1);
    ctx.restore();
  },
  themeApiVersion: 1,
};
