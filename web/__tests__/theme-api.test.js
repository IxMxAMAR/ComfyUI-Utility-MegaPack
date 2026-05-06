import { describe, it, expect, beforeEach, vi } from "vitest";
import { createThemeApi } from "../theme-api.js";

describe("themeApi.motionAllowed", () => {
  let settings, prefersReducedMotion;

  beforeEach(() => {
    settings = { reduceMotion: false, heavyThemeNodeBudget: 60 };
    prefersReducedMotion = false;
    vi.spyOn(window, "matchMedia").mockImplementation((query) => ({
      matches: query.includes("prefers-reduced-motion") && prefersReducedMotion,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    }));
  });

  it("allows motion when no gate is active", () => {
    const api = createThemeApi({ settings, getVisibleThemedCount: () => 5 });
    expect(api.motionAllowed("low")).toBe(true);
    expect(api.motionAllowed("high")).toBe(true);
  });

  it("blocks motion when prefers-reduced-motion is set", () => {
    prefersReducedMotion = true;
    const api = createThemeApi({ settings, getVisibleThemedCount: () => 5 });
    expect(api.motionAllowed("low")).toBe(false);
  });

  it("blocks motion when settings.reduceMotion is on", () => {
    settings.reduceMotion = true;
    const api = createThemeApi({ settings, getVisibleThemedCount: () => 5 });
    expect(api.motionAllowed("low")).toBe(false);
  });

  it("blocks motion when visible themed count exceeds budget", () => {
    const api = createThemeApi({ settings, getVisibleThemedCount: () => 100 });
    expect(api.motionAllowed("low")).toBe(false);
  });

  it("'none' level blocks all motion regardless of gates", () => {
    const api = createThemeApi({ settings, getVisibleThemedCount: () => 5 });
    expect(api.motionAllowed("none")).toBe(false);
  });
});
