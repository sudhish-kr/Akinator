/** Display helpers for backend confidence (0–1 posterior). */

/**
 * Format confidence for the HUD.
 * Uses the real posterior — never invents progress.
 * Sub-1% values keep one decimal so the bar is not stuck at "0%".
 */
export function formatConfidencePercent(confidence) {
  const c = Number(confidence);
  if (!Number.isFinite(c) || c <= 0) return 0;
  const clamped = Math.min(1, c);
  if (clamped < 0.01) {
    return Math.round(clamped * 1000) / 10;
  }
  return Math.round(clamped * 100);
}

/** Apply the latest API confidence; never keep a stale value. */
export function nextConfidence(previous, incoming) {
  if (incoming === undefined || incoming === null) {
    return typeof previous === "number" ? previous : 0;
  }
  const c = Number(incoming);
  return Number.isFinite(c) ? Math.max(0, Math.min(1, c)) : 0;
}
