import { describe, it, expect } from "vitest";
import { resolveCategoryAccent } from "../theme-engine.js";

describe("resolveCategoryAccent", () => {
  const accents = {
    image: "#06ffa5",
    latent: "#c084fc",
    conditioning: "#ffd93d",
    default: "#888888",
  };

  it("matches the first path segment", () => {
    const node = { constructor: { category: "image/upscaling" } };
    expect(resolveCategoryAccent(node, accents)).toBe("#06ffa5");
  });

  it("matches a single-segment category", () => {
    const node = { constructor: { category: "latent" } };
    expect(resolveCategoryAccent(node, accents)).toBe("#c084fc");
  });

  it("matches a later segment if the first doesn't have an accent", () => {
    const node = { constructor: { category: "samplers/conditioning" } };
    expect(resolveCategoryAccent(node, accents)).toBe("#ffd93d");
  });

  it("falls back to `default` when nothing matches", () => {
    const node = { constructor: { category: "weird/unknown/path" } };
    expect(resolveCategoryAccent(node, accents)).toBe("#888888");
  });

  it("returns null when there's no default and no match", () => {
    const node = { constructor: { category: "weird" } };
    expect(resolveCategoryAccent(node, { image: "#abc" })).toBeNull();
  });

  it("handles nodes with no category", () => {
    const node = { constructor: {} };
    expect(resolveCategoryAccent(node, accents)).toBe("#888888");
  });

  it("is case-insensitive on category names", () => {
    const node = { constructor: { category: "IMAGE/Upscaling" } };
    expect(resolveCategoryAccent(node, accents)).toBe("#06ffa5");
  });
});
