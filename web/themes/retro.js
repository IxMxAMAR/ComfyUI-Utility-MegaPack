import { cachedPattern } from "../cache.js";

const ID = "retro_terminal";

export default {
  id: ID,
  displayName: "Retro Terminal",
  motion: "none",
  staticConfig: {
    bgcolor: "#0a1a0a",
    color: "#2dff52",
    titlecolor: "#2dff52",
    titletext: "#0a1a0a",
    boxcolor: "#2dff52",
  },
  wirePalette: {
    default: "#2dff52",
    IMAGE: "#88ff99",
    LATENT: "#33dd88",
  },
  categoryAccents: {
    image: "#88ff99",
    default: "#2dff52",
  },
  groupColors: { color: "#2dff52", bgcolor: "#0a1a0a" },
  bgGridColor: "#0a1a0a",
  drawForeground(ctx, node) {
    const w = node.size?.[0] ?? 0;
    const h = node.size?.[1] ?? 0;
    if (w <= 0 || h <= 0) return;
    // Cached scanline overlay — drawn once per (w, h), blitted thereafter.
    // v0.1.x looped through every 3rd y-row per draw frame; now it's one
    // drawImage call.
    const scanlines = cachedPattern(node, ID, w, h, (octx, ow, oh) => {
      octx.globalAlpha = 0.04;
      octx.fillStyle = "#2dff52";
      for (let y = 0; y < oh; y += 3) octx.fillRect(0, y, ow, 1);
    });
    if (scanlines) ctx.drawImage(scanlines, 0, 0);
  },
  themeApiVersion: 2,
};
