const MP_CLASS_PREFIX = "UtilMegaPack_";
const PACK_DEFAULT = "(use pack default)";
const COMFY_DEFAULT = "(use ComfyUI default)";

function isMegaPackNode(node) {
  return typeof node.comfyClass === "string" && node.comfyClass.startsWith(MP_CLASS_PREFIX);
}

function hasCustomDrawing(node) {
  return typeof node.onDrawForeground === "function";
}

export function resolveTheme(node, settings) {
  const own = node.properties?.megapack_theme;

  if (own && own !== PACK_DEFAULT && own !== COMFY_DEFAULT) {
    return own;
  }

  if (own === COMFY_DEFAULT) {
    return settings.globalOverrideEnabled ? settings.globalTheme : null;
  }

  if (isMegaPackNode(node)) {
    return settings.packDefault;
  }

  if (settings.globalOverrideEnabled) {
    if (settings.respectExistingCustomDrawing && hasCustomDrawing(node)) {
      return null;
    }
    return settings.globalTheme;
  }

  return null;
}
