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
  drawForeground(ctx, node, themeApi) {
    if (!themeApi || !themeApi.motionAllowed("low")) return;
    const w = node.size?.[0] ?? 0;
    const h = node.size?.[1] ?? 0;
    if (w <= 0 || h <= 0) return;
    ctx.save();
    ctx.shadowColor = "rgba(189,147,249,0.3)";
    ctx.shadowBlur = 14;
    ctx.strokeStyle = "rgba(189,147,249,0)";
    ctx.strokeRect(0, 0, w, h);
    ctx.restore();
  },
  themeApiVersion: 1,
};
