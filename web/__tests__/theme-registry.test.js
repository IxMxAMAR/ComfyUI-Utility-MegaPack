import { describe, it, expect, beforeEach } from "vitest";
import { ThemeRegistry } from "../theme-registry.js";

describe("ThemeRegistry", () => {
  let reg;
  beforeEach(() => { reg = new ThemeRegistry(); });

  it("starts empty", () => {
    expect(reg.size).toBe(0);
    expect(reg.get("anything")).toBeUndefined();
  });

  it("registers and retrieves themes by id", () => {
    reg.register({ id: "cyberpunk", displayName: "Cyberpunk", motion: "low" });
    expect(reg.get("cyberpunk").displayName).toBe("Cyberpunk");
    expect(reg.size).toBe(1);
  });

  it("rejects duplicate ids", () => {
    reg.register({ id: "x", displayName: "X" });
    expect(() => reg.register({ id: "x", displayName: "Y" })).toThrow(/duplicate theme id/);
  });

  it("rejects themes missing id", () => {
    expect(() => reg.register({ displayName: "X" })).toThrow(/missing 'id'/);
  });

  it("ids() returns sorted list", () => {
    reg.register({ id: "zebra" });
    reg.register({ id: "apple" });
    expect(reg.ids()).toEqual(["apple", "zebra"]);
  });
});
