import { describe, it, expect, beforeEach } from "vitest";
import { ThemeEngine } from "../theme-engine.js";

function makeNode(initial = {}) {
  return {
    bgcolor: initial.bgcolor ?? "#353535",
    color: initial.color ?? "#2a2a2a",
    boxcolor: initial.boxcolor ?? "#888",
    titlecolor: initial.titlecolor ?? "#fff",
    shape: initial.shape ?? 1,
    onDrawForeground: initial.onDrawForeground,
    onDrawBackground: initial.onDrawBackground,
    setDirtyCanvas: () => {},
  };
}

describe("ThemeEngine.applyTheme", () => {
  let engine;
  beforeEach(() => { engine = new ThemeEngine({ themeApi: { motionAllowed: () => true } }); });

  it("applies static config to the node", () => {
    const node = makeNode();
    engine.applyTheme(node, {
      id: "cyber",
      staticConfig: { bgcolor: "#0a0612", color: "#1a0a2a" },
    });
    expect(node.bgcolor).toBe("#0a0612");
    expect(node.color).toBe("#1a0a2a");
  });

  it("wraps onDrawForeground when theme provides one", () => {
    const node = makeNode();
    let called = false;
    engine.applyTheme(node, {
      id: "x",
      staticConfig: {},
      drawForeground(ctx) { called = true; },
    });
    node.onDrawForeground({});
    expect(called).toBe(true);
  });

  it("preserves original onDrawForeground when wrapping", () => {
    let originalCalled = false;
    const node = makeNode({
      onDrawForeground() { originalCalled = true; },
    });
    engine.applyTheme(node, {
      id: "x",
      staticConfig: {},
      drawForeground() {},
    });
    node.onDrawForeground({});
    expect(originalCalled).toBe(true);
  });

  it("re-applying the same theme is idempotent (does NOT stack wrappers)", () => {
    let drawCount = 0;
    const node = makeNode();
    const theme = {
      id: "x",
      staticConfig: {},
      drawForeground() { drawCount++; },
    };
    engine.applyTheme(node, theme);
    engine.applyTheme(node, theme);
    engine.applyTheme(node, theme);
    node.onDrawForeground({});
    expect(drawCount).toBe(1);
  });

  it("switching themes restores originals before applying new draw hooks", () => {
    const node = makeNode();
    let aCount = 0, bCount = 0;
    engine.applyTheme(node, {
      id: "a", staticConfig: { bgcolor: "#a" },
      drawForeground() { aCount++; },
    });
    engine.applyTheme(node, {
      id: "b", staticConfig: { bgcolor: "#b" },
      drawForeground() { bCount++; },
    });
    node.onDrawForeground({});
    expect(aCount).toBe(0);
    expect(bCount).toBe(1);
    expect(node.bgcolor).toBe("#b");
  });

  it("applying null theme restores original state", () => {
    const node = makeNode({ bgcolor: "#orig" });
    engine.applyTheme(node, { id: "x", staticConfig: { bgcolor: "#new" } });
    expect(node.bgcolor).toBe("#new");
    engine.applyTheme(node, null);
    expect(node.bgcolor).toBe("#orig");
  });

  it("'default' theme id is treated as null (vanilla render)", () => {
    const node = makeNode({ bgcolor: "#orig" });
    engine.applyTheme(node, { id: "x", staticConfig: { bgcolor: "#new" } });
    engine.applyTheme(node, { id: "default", staticConfig: {} });
    expect(node.bgcolor).toBe("#orig");
  });
});
