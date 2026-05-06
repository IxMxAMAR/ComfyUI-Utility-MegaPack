import { describe, it, expect } from "vitest";
import { resolveTheme } from "../resolve-theme.js";

const MP_NODE = (overrides = {}) => ({
  comfyClass: "UtilMegaPack_Programming",
  properties: {},
  onDrawForeground: undefined,
  ...overrides,
});

const NON_MP_NODE = (overrides = {}) => ({
  comfyClass: "OtherPack_Foo",
  properties: {},
  onDrawForeground: undefined,
  ...overrides,
});

describe("resolveTheme cascade", () => {
  const settings = {
    packDefault: "minimalist",
    globalOverrideEnabled: false,
    globalTheme: "cyberpunk",
    respectExistingCustomDrawing: true,
  };

  it("explicit per-node theme wins over everything", () => {
    const node = MP_NODE({ properties: { megapack_theme: "dracula" } });
    expect(resolveTheme(node, settings)).toBe("dracula");
  });

  it("'(use pack default)' on MP node falls back to packDefault", () => {
    const node = MP_NODE({ properties: { megapack_theme: "(use pack default)" } });
    expect(resolveTheme(node, settings)).toBe("minimalist");
  });

  it("MP node with no megapack_theme property falls back to packDefault", () => {
    const node = MP_NODE();
    expect(resolveTheme(node, settings)).toBe("minimalist");
  });

  it("'(use ComfyUI default)' returns null when global override is off", () => {
    const node = MP_NODE({ properties: { megapack_theme: "(use ComfyUI default)" } });
    expect(resolveTheme(node, settings)).toBeNull();
  });

  it("'(use ComfyUI default)' returns globalTheme when override is on", () => {
    const node = MP_NODE({ properties: { megapack_theme: "(use ComfyUI default)" } });
    const s = { ...settings, globalOverrideEnabled: true };
    expect(resolveTheme(node, s)).toBe("cyberpunk");
  });

  it("non-MP node returns null when override is off", () => {
    const node = NON_MP_NODE();
    expect(resolveTheme(node, settings)).toBeNull();
  });

  it("non-MP node returns globalTheme when override is on", () => {
    const node = NON_MP_NODE();
    const s = { ...settings, globalOverrideEnabled: true };
    expect(resolveTheme(node, s)).toBe("cyberpunk");
  });

  it("non-MP node with custom drawing is skipped when respectExistingCustomDrawing is on", () => {
    const node = NON_MP_NODE({ onDrawForeground: () => {} });
    const s = { ...settings, globalOverrideEnabled: true, respectExistingCustomDrawing: true };
    expect(resolveTheme(node, s)).toBeNull();
  });

  it("non-MP node with custom drawing IS themed when respect toggle is off", () => {
    const node = NON_MP_NODE({ onDrawForeground: () => {} });
    const s = { ...settings, globalOverrideEnabled: true, respectExistingCustomDrawing: false };
    expect(resolveTheme(node, s)).toBe("cyberpunk");
  });
});
