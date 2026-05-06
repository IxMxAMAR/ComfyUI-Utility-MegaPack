export function createThemeApi({ settings, getVisibleThemedCount }) {
  return {
    motionAllowed(level) {
      if (level === "none") return false;
      if (settings.reduceMotion) return false;
      if (typeof window !== "undefined" && window.matchMedia) {
        const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
        if (mq.matches) return false;
      }
      if (getVisibleThemedCount() > settings.heavyThemeNodeBudget) return false;
      return true;
    },
  };
}
