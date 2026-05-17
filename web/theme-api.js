export function createThemeApi({ settings, getVisibleThemedCount }) {
  // Evaluate prefers-reduced-motion ONCE at construction. Calling
  // window.matchMedia() inside the hot path was allocating a new
  // MediaQueryList per themed-node per frame (≈20k allocs/sec at 200Hz
  // with globalOverrideEnabled), which collapsed the canvas to ~25 FPS.
  // We listen for OS-level changes asynchronously instead.
  let prefersReducedMotion = false;
  if (typeof window !== "undefined" && window.matchMedia) {
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    prefersReducedMotion = mq.matches;
    const onChange = (e) => { prefersReducedMotion = e.matches; };
    if (mq.addEventListener) mq.addEventListener("change", onChange);
    else if (mq.addListener) mq.addListener(onChange); // legacy Safari
  }

  return {
    motionAllowed(level) {
      if (level === "none") return false;
      if (settings.reduceMotion) return false;
      if (prefersReducedMotion) return false;
      if (getVisibleThemedCount() > settings.heavyThemeNodeBudget) return false;
      return true;
    },
  };
}
