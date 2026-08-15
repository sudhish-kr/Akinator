/** Short UI beats for the final-guess screen. Does not change guessing logic. */

export const FOCUS_MS = 420;
export const CELEBRATE_MS = 480;
export const MISS_MS = 380;

export function prefersReducedMotion() {
  try {
    return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  } catch {
    return false;
  }
}

export function beatMs(kind, reduced = false) {
  if (reduced) return 0;
  if (kind === "focus") return FOCUS_MS;
  if (kind === "celebrate") return CELEBRATE_MS;
  if (kind === "miss") return MISS_MS;
  return 0;
}
