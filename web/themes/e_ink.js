import { cachedPattern } from "../cache.js";

const ID = "e_ink";

// Deterministic pseudo-random for the noise pattern. seed is unused but the
// pattern depends only on (x, y) so all nodes look like the same paper.
function noiseAt(x, y) {
  const v = (x * 73856093) ^ (y * 19349663);
  return ((v >>> 0) % 100) / 100;
}

export default {
  id: ID,
  displayName: "E-Ink",
  motion: "none",
  staticConfig: {
    bgcolor: "#f4f4f4",
    color: "#e0e0e0",
    titlecolor: "#e0e0e0",
    titletext: "#000000",
    boxcolor: "#000000",
  },
  wirePalette: {
    default: "#000000",
    IMAGE: "#404040",
    LATENT: "#606060",
    MASK: "#808080",
    CONDITIONING: "#202020",
  },
  categoryAccents: {
    image: "#000000",
    latent: "#404040",
    conditioning: "#606060",
    default: "#000000",
  },
  groupColors: { color: "#000000", bgcolor: "#e8e8e8" },
  bgGridColor: "#ebebeb",
  drawForeground(ctx, node) {
    const w = node.size?.[0] ?? 0;
    const h = node.size?.[1] ?? 0;
    if (w <= 0 || h <= 0) return;
    // Cached low-frequency noise overlay (mimics e-paper texture).
    const noise = cachedPattern(node, ID, w, h, (octx, ow, oh) => {
      const img = octx.createImageData(ow, oh);
      for (let y = 0; y < oh; y++) {
        for (let x = 0; x < ow; x++) {
          // Only draw noise on ~3% of pixels — very sparse dithering.
          if (noiseAt(x, y) < 0.03) {
            const i = (y * ow + x) * 4;
            img.data[i] = 0;
            img.data[i + 1] = 0;
            img.data[i + 2] = 0;
            img.data[i + 3] = 40;
          }
        }
      }
      octx.putImageData(img, 0, 0);
    });
    if (noise) ctx.drawImage(noise, 0, 0);
  },
  themeApiVersion: 2,
};
