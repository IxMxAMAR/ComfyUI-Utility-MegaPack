import { cachedPattern } from "../cache.js";

const ID = "blueprint";

export default {
  id: ID,
  displayName: "Blueprint",
  motion: "none",
  staticConfig: {
    bgcolor: "#0d47a1",
    color: "#082f6b",
    titlecolor: "#082f6b",
    titletext: "#ffffff",
    boxcolor: "#ffffff",
  },
  wirePalette: {
    default: "#ffffff",
    IMAGE: "#a3d4ff",
    LATENT: "#ffd54f",
    MASK: "#ffffff",
    CONDITIONING: "#ffab40",
  },
  categoryAccents: {
    image: "#a3d4ff",
    latent: "#ffd54f",
    conditioning: "#ffab40",
    sampling: "#80cbc4",
    default: "#ffffff",
  },
  groupColors: { color: "#ffffff", bgcolor: "#082f6b" },
  bgGridColor: "#0a3781",
  drawForeground(ctx, node) {
    const w = node.size?.[0] ?? 0;
    const h = node.size?.[1] ?? 0;
    if (w <= 0 || h <= 0) return;
    // Faint white grid overlay, cached per (theme, w, h).
    const grid = cachedPattern(node, ID, w, h, (octx, ow, oh) => {
      octx.globalAlpha = 0.08;
      octx.strokeStyle = "#ffffff";
      octx.lineWidth = 1;
      octx.beginPath();
      for (let x = 12; x < ow; x += 12) {
        octx.moveTo(x + 0.5, 0);
        octx.lineTo(x + 0.5, oh);
      }
      for (let y = 12; y < oh; y += 12) {
        octx.moveTo(0, y + 0.5);
        octx.lineTo(ow, y + 0.5);
      }
      octx.stroke();
    });
    if (grid) ctx.drawImage(grid, 0, 0);
  },
  themeApiVersion: 2,
};
