import { app } from "../../scripts/app.js";

import { ThemeRegistry } from "./theme-registry.js";
import { ThemeEngine, applyGlobalTweaks, applyThemeToGroup } from "./theme-engine.js";
import { createThemeApi } from "./theme-api.js";
import { resolveTheme } from "./resolve-theme.js";
import {
  applyWirePalette,
  applyWireRenderMode,
  applyWireThickness,
  setWireOpacity,
  ensureRenderLinkWrapped,
} from "./wire-engine.js";

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
// v0.2.0 additions:
import blueprint from "./themes/blueprint.js";
import nord from "./themes/nord.js";
import synthwave from "./themes/synthwave.js";
import eInk from "./themes/e_ink.js";

export const THEME_API_VERSION = 2;

const registry = new ThemeRegistry();
for (const theme of [
  cyberpunk, minimalist, glassmorphic, retro, defaultTheme,
  holographic, paper, brutalist, solarized, dracula, highContrast,
  blueprint, nord, synthwave, eInk,
]) {
  registry.register(theme);
}

const settings = {
  packDefault: "default",
  globalOverrideEnabled: false,
  globalTheme: "default",
  respectExistingCustomDrawing: true,
  reduceMotion: false,
  heavyThemeNodeBudget: 25,
  // v0.2.0
  wireRenderMode: null,  // null = leave ComfyUI's setting alone; otherwise a LiteGraph constant (-1, 0, 1, or 2)
  wireThickness: 1.0,    // multiplier on default line width
  wireOpacity: 1.0,      // 0..1
  // v0.3.0
  autoContrastText: true,
  rightClickThemeMenu: true,
};

const themedNodes = new Set();

const themeApi = createThemeApi({
  settings,
  getVisibleThemedCount: () => themedNodes.size,
});

const engine = new ThemeEngine({ themeApi });


function activeGlobalTheme() {
  // The theme that drives global tweaks (wires, groups, canvas bg). When
  // override is on, that's the global theme; otherwise it's the pack default.
  const id = settings.globalOverrideEnabled ? settings.globalTheme : settings.packDefault;
  return id && id !== "default" ? registry.get(id) : null;
}


function syncGlobalTweaks() {
  const theme = activeGlobalTheme();
  applyWirePalette(app, theme?.wirePalette ?? null);
  applyGlobalTweaks(app, theme);
}


function applyResolved(node) {
  const themeId = resolveTheme(node, settings);
  const theme = themeId ? registry.get(themeId) : null;
  if (theme) theme.themeApi = themeApi;
  engine.applyTheme(node, theme, { autoContrast: settings.autoContrastText });
  if (theme) themedNodes.add(node);
  else themedNodes.delete(node);
}


function reapplyAll() {
  if (!app.graph || !app.graph._nodes) return;
  // Apply per-node themes first (controls accent stripes + foregrounds).
  for (const node of app.graph._nodes) applyResolved(node);
  // Then sync global tweaks (wire palette, group colors, canvas bg).
  syncGlobalTweaks();
}


const THEME_OPTIONS = registry.ids();

// Wire render modes — explicit label→value pairs because LiteGraph's constants
// are 0-based AND non-contiguous (HIDDEN=-1, STRAIGHT=0, LINEAR=1, SPLINE=2).
// v0.3.0 used `indexOf` on a label-only array which was off-by-one and also
// included a fictional "manhattan" option. The result: 3 of 4 options either
// did the wrong thing or did nothing. The selected "straight" looked plausible
// because it actually set LINEAR.
const WIRE_RENDER_MODES = [
  { label: "off (leave ComfyUI's setting)", value: null },
  { label: "hidden",                         value: -1   },
  { label: "straight",                       value: 0    },
  { label: "linear",                         value: 1    },
  { label: "spline (bezier)",                value: 2    },
];
const WIRE_RENDER_MODE_OPTIONS = WIRE_RENDER_MODES.map((m) => m.label);
const wireRenderValueFor = (label) =>
  WIRE_RENDER_MODES.find((m) => m.label === label)?.value ?? null;

function defineSetting(id, name, type, defaultValue, onChange, options) {
  const setting = {
    id: `megapack.${id}`,
    name,
    type,
    defaultValue,
    onChange,
  };
  if (type === "combo" && Array.isArray(options)) {
    setting.options = options;
  }
  app.ui.settings.addSetting(setting);
}


app.registerExtension({
  name: "UtilityMegaPack.ThemeEngine",

  async setup() {
    // Wire-engine patch is installed ONCE at startup. It reads live settings,
    // so subsequent setting changes take effect without re-patching.
    if (typeof window !== "undefined" && window.LGraphCanvas) {
      ensureRenderLinkWrapped(window.LGraphCanvas);
    }

    // Auto-theme any groups created AFTER a global theme is active. v0.2.x
    // only applied group colors on theme switch, so new groups showed
    // LiteGraph defaults until the user re-picked the theme.
    if (app.graph) {
      const origOnGroupAdded = app.graph.onGroupAdded;
      app.graph.onGroupAdded = function (group) {
        applyThemeToGroup(group);
        if (origOnGroupAdded) origOnGroupAdded.call(this, group);
      };
    }

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
      25,
      (v) => { settings.heavyThemeNodeBudget = v; app.canvas?.setDirty?.(true, true); });

    // v0.2.0: wire/connection theming
    defineSetting("wireRenderMode", "Utility-MegaPack — Wire render mode", "combo",
      WIRE_RENDER_MODE_OPTIONS[0],
      (v) => {
        const val = wireRenderValueFor(v);
        settings.wireRenderMode = val;
        if (val !== null) {
          applyWireRenderMode(app, val);
        }
      },
      WIRE_RENDER_MODE_OPTIONS);
    defineSetting("wireThickness", "Utility-MegaPack — Wire thickness (×)", "number",
      1.0,
      (v) => { settings.wireThickness = Number(v) || 1.0; applyWireThickness(app, settings.wireThickness); });
    defineSetting("wireOpacity", "Utility-MegaPack — Wire opacity", "slider",
      1.0,
      (v) => { settings.wireOpacity = Number(v) || 1.0; setWireOpacity(settings.wireOpacity); app.canvas?.setDirty?.(true, false); });
    // v0.3.0: UX
    defineSetting("autoContrastText", "Utility-MegaPack — Auto-contrast title text", "boolean",
      true,
      (v) => { settings.autoContrastText = !!v; reapplyAll(); });
    defineSetting("rightClickThemeMenu", "Utility-MegaPack — Right-click 'Theme…' menu on nodes", "boolean",
      true,
      (v) => { settings.rightClickThemeMenu = !!v; });
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
        syncGlobalTweaks();
        return orig?.(v, ...rest);
      };
    }
    // Right-click → "Theme…" submenu. Lets users theme ANY node without
    // a widget (vanilla ComfyUI nodes don't have a theme widget at all).
    const origMenu = node.getExtraMenuOptions;
    node.getExtraMenuOptions = function (canvas, options) {
      if (origMenu) origMenu.call(this, canvas, options);
      if (!settings.rightClickThemeMenu) return;
      const submenu = THEME_OPTIONS.map((id) => ({
        content: id === "default" ? "(default — no theme)" : id,
        callback: () => {
          this.properties = this.properties ?? {};
          this.properties.megapack_theme = id;
          applyResolved(this);
          syncGlobalTweaks();
          this.setDirtyCanvas?.(true, true);
        },
      }));
      const active = this.properties?.megapack_theme;
      for (const item of submenu) {
        if (item.content.startsWith(active || "")) item.content = "• " + item.content;
      }
      options.push(null);  // visual separator
      options.push({
        content: "Theme…",
        has_submenu: true,
        submenu: { options: submenu },
      });
    };
  },

  async loadedGraphNode(node) {
    applyResolved(node);
    // After the full graph loads, sync global tweaks once (group colors etc.)
    syncGlobalTweaks();
  },

  // Without this, deleted nodes lingered in `themedNodes` forever — leaking
  // references AND permanently inflating the heavyThemeNodeBudget check, which
  // would eventually disable all motion across the session.
  nodeRemoved(node) {
    themedNodes.delete(node);
  },
});
