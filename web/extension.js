import { app } from "../../scripts/app.js";

import { ThemeRegistry } from "./theme-registry.js";
import { ThemeEngine } from "./theme-engine.js";
import { createThemeApi } from "./theme-api.js";
import { resolveTheme } from "./resolve-theme.js";

import cyberpunk from "./themes/cyberpunk.js";
import minimalist from "./themes/minimalist.js";
import glassmorphic from "./themes/glassmorphic.js";
import retro from "./themes/retro.js";
import defaultTheme from "./themes/default.js";
import holographic from "./themes/holographic.js";
import paper from "./themes/paper.js";
import brutalist from "./themes/brutalist.js";
import solarized from "./themes/solarized.js";
import dracula from "./themes/dracula.js";
import highContrast from "./themes/high_contrast.js";

export const THEME_API_VERSION = 1;

const registry = new ThemeRegistry();
for (const theme of [
  cyberpunk, minimalist, glassmorphic, retro, defaultTheme,
  holographic, paper, brutalist, solarized, dracula, highContrast,
]) {
  registry.register(theme);
}

const settings = {
  packDefault: "default",
  globalOverrideEnabled: false,
  globalTheme: "default",
  respectExistingCustomDrawing: true,
  reduceMotion: false,
  // Lowered from 60 in v0.1.3 — even with the cheaper stroke-based glow,
  // running animated themes across 25+ nodes per frame can dent framerate
  // on lower-end GPUs. Raise this manually if you're on a beefy machine.
  heavyThemeNodeBudget: 25,
};

const themedNodes = new Set();

const themeApi = createThemeApi({
  settings,
  getVisibleThemedCount: () => themedNodes.size,
});

const engine = new ThemeEngine({ themeApi });

function applyResolved(node) {
  const themeId = resolveTheme(node, settings);
  const theme = themeId ? registry.get(themeId) : null;
  if (theme) theme.themeApi = themeApi;
  engine.applyTheme(node, theme);
  if (theme) themedNodes.add(node);
  else themedNodes.delete(node);
}

function reapplyAll() {
  if (!app.graph || !app.graph._nodes) return;
  for (const node of app.graph._nodes) applyResolved(node);
}

// Theme IDs available as combo options. Kept in sync with registered themes.
const THEME_OPTIONS = registry.ids();

function defineSetting(id, name, type, defaultValue, onChange, options) {
  const setting = {
    id: `megapack.${id}`,
    name,
    type,
    defaultValue,
    onChange,
  };
  // ComfyUI's settings API requires `options` for combo-type settings;
  // without it the dropdown renders empty (Gemini review #4).
  if (type === "combo" && Array.isArray(options)) {
    setting.options = options;
  }
  app.ui.settings.addSetting(setting);
}

app.registerExtension({
  name: "UtilityMegaPack.ThemeEngine",

  async setup() {
    defineSetting("packDefault", "Utility-MegaPack — Pack default theme", "combo",
      "default",
      (v) => { settings.packDefault = v; reapplyAll(); },
      THEME_OPTIONS);
    defineSetting("globalOverrideEnabled", "Utility-MegaPack — Theme ALL ComfyUI nodes", "boolean",
      false,
      (v) => { settings.globalOverrideEnabled = v; reapplyAll(); });
    defineSetting("globalTheme", "Utility-MegaPack — Global theme", "combo",
      "default",
      (v) => { settings.globalTheme = v; reapplyAll(); },
      THEME_OPTIONS);
    defineSetting("respectExistingCustomDrawing", "Utility-MegaPack — Respect existing custom drawing", "boolean",
      true,
      (v) => { settings.respectExistingCustomDrawing = v; reapplyAll(); });
    defineSetting("reduceMotion", "Utility-MegaPack — Reduce motion", "boolean",
      false,
      (v) => { settings.reduceMotion = v; reapplyAll(); });
    defineSetting("heavyThemeNodeBudget", "Utility-MegaPack — Heavy theme node budget", "number",
      60,
      (v) => { settings.heavyThemeNodeBudget = v; });
  },

  async nodeCreated(node) {
    applyResolved(node);
    const themeWidget = node.widgets?.find((w) => w.name === "theme");
    if (themeWidget) {
      const orig = themeWidget.callback;
      themeWidget.callback = (v, ...rest) => {
        node.properties = node.properties ?? {};
        node.properties.megapack_theme = v;
        applyResolved(node);
        return orig?.(v, ...rest);
      };
    }
  },

  async loadedGraphNode(node) { applyResolved(node); },
});
