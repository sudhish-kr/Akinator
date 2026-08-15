/**
 * Pure helpers for home-world ball proximity reactions.
 * No React state; callers drive DOM/CSS from these values.
 */

export const BALL_PALETTE = [
  { id: "teal", tint: "#3aa89a" },
  { id: "blue", tint: "#4d90c9" },
  { id: "purple", tint: "#8a6bb8" },
  { id: "yellow", tint: "#d4b24a" },
  { id: "coral", tint: "#e07a6a" },
  { id: "mint", tint: "#5cb88a" },
];

/** Radius grows with ball size, clamped for desktop feel. */
export function proximityRadius(size) {
  const n = Number(size) || 48;
  return Math.round(Math.max(80, Math.min(130, n * 1.15 + 55)));
}

export function isInsideProximity(dx, dy, radius, hysteresis = 1) {
  const r = (radius || 0) * hysteresis;
  return dx * dx + dy * dy <= r * r;
}

/** Subtle look toward the cursor — not 1:1 tracking. */
export function lookOffset(dx, dy, radius) {
  const r = radius || 1;
  const nx = Math.max(-1, Math.min(1, dx / r));
  const ny = Math.max(-1, Math.min(1, dy / r));
  return {
    x: Math.round(nx * 24) / 10,
    y: Math.round(ny * 18) / 10,
  };
}

export function pickBallColor(excludeId, random = Math.random) {
  const pool = BALL_PALETTE.filter((c) => c.id !== excludeId);
  const list = pool.length ? pool : BALL_PALETTE;
  return list[Math.floor(random() * list.length)];
}

/** Trigger once on enter; again only after leave + cooldown. */
export function shouldActivate({ inside, wasInside, now, cooldownUntil }) {
  return Boolean(inside && !wasInside && now >= (cooldownUntil || 0));
}

export const BALL_MOODS = ["happy", "excited", "curious"];

export function pickBallMood(exclude, random = Math.random) {
  const pool = BALL_MOODS.filter((m) => m !== exclude);
  const list = pool.length ? pool : BALL_MOODS;
  return list[Math.floor(random() * list.length)];
}

export function staggerDelay(indexInFrame) {
  if (!indexInFrame) return 0;
  return indexInFrame * 55;
}
