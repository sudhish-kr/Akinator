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

export const BALL_MOODS = ["happy", "excited", "curious"];

export const BURST_MS = 360;
export const ARRIVE_MS = 280;

export const UI_KEEP_OUT_SELECTORS = [
  ".home-content",
  ".home-start",
  ".home-actions",
  ".admin-entry",
  ".lang-switch-floating",
];

/** Radius grows with ball size, clamped so proximity (not a direct hit) triggers. */
export function proximityRadius(size) {
  const n = Number(size) || 48;
  return Math.round(Math.max(60, Math.min(100, n * 0.55 + 52)));
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

export function pickBallMood(exclude, random = Math.random) {
  const pool = BALL_MOODS.filter((m) => m !== exclude);
  const list = pool.length ? pool : BALL_MOODS;
  return list[Math.floor(random() * list.length)];
}

export function staggerDelay(indexInFrame) {
  if (!indexInFrame) return 0;
  return indexInFrame * 55;
}

export function jitterSize(size, random = Math.random) {
  const jitter = 0.82 + random() * 0.36;
  return Math.round(Math.max(22, Math.min(96, (Number(size) || 48) * jitter)));
}

export function jitterDuration(duration, random = Math.random) {
  return Math.round((Number(duration) || 6) * (0.85 + random() * 0.35) * 10) / 10;
}

export function jitterOpacity(depth, random = Math.random) {
  const base = 0.42 + (Number(depth) || 1) * 0.22;
  return Math.round(Math.min(0.82, Math.max(0.28, base + (random() - 0.5) * 0.2)) * 100) / 100;
}

export function isClearOfPoint(px, py, point, minDist) {
  if (!point) return true;
  const dist = Number(minDist) || 0;
  return Math.hypot(px - point.x, py - point.y) >= dist;
}

export function rectsOverlap(a, b, pad = 0) {
  if (!a || !b) return false;
  const p = Number(pad) || 0;
  return !(
    a.right + p < b.left ||
    a.left - p > b.right ||
    a.bottom + p < b.top ||
    a.top - p > b.bottom
  );
}

export function collectKeepOutRects(root) {
  if (typeof document === "undefined") return [];
  const home = root?.closest?.(".home") || root;
  const doc = (home && home.ownerDocument) || document;
  const rects = [];
  for (const selector of UI_KEEP_OUT_SELECTORS) {
    const searchRoot = selector === ".lang-switch-floating" ? doc : home || doc;
    if (!searchRoot?.querySelectorAll) continue;
    searchRoot.querySelectorAll(selector).forEach((node) => {
      const box = node.getBoundingClientRect();
      if (box.width > 2 && box.height > 2) rects.push(box);
    });
  }
  return rects;
}

function ballBoxAt(px, py, size) {
  const half = (Number(size) || 48) / 2;
  return {
    left: px - half,
    top: py - half,
    right: px + half,
    bottom: py + half,
  };
}

/** Percent coordinates far enough from the cursor and outside main UI. */
export function pickSpawnPercent({
  rootRect,
  mouse,
  avoidRects = [],
  size = 48,
  random = Math.random,
  attempts = 28,
} = {}) {
  if (!rootRect || rootRect.width < 8 || rootRect.height < 8) {
    return { x: 8 + random() * 84, y: 10 + random() * 80 };
  }
  const minMouse = proximityRadius(size) + 48;
  const point = mouse ? { x: mouse.clientX, y: mouse.clientY } : null;

  const tryPoint = (xPct, yPct) => {
    const px = rootRect.left + (xPct / 100) * rootRect.width;
    const py = rootRect.top + (yPct / 100) * rootRect.height;
    if (!isClearOfPoint(px, py, point, minMouse)) return null;
    const box = ballBoxAt(px, py, size);
    if (avoidRects.some((rect) => rectsOverlap(box, rect, 18))) return null;
    return {
      x: Math.round(xPct * 10) / 10,
      y: Math.round(yPct * 10) / 10,
    };
  };

  for (let i = 0; i < attempts; i += 1) {
    const hit = tryPoint(6 + random() * 88, 8 + random() * 84);
    if (hit) return hit;
  }

  const corners = [
    [8, 10],
    [92, 10],
    [8, 88],
    [92, 88],
  ];
  let best = { x: 8, y: 10 };
  let bestDist = -1;
  for (const [xPct, yPct] of corners) {
    const px = rootRect.left + (xPct / 100) * rootRect.width;
    const py = rootRect.top + (yPct / 100) * rootRect.height;
    const dist = point ? Math.hypot(px - point.x, py - point.y) : 0;
    if (dist >= bestDist) {
      bestDist = dist;
      best = { x: xPct, y: yPct };
    }
  }
  return best;
}

export function nextBallSpec(prev, spawn, random = Math.random) {
  const size = spawn.size ?? jitterSize(prev.baseSize ?? prev.size, random);
  return {
    size,
    x: spawn.x,
    y: spawn.y,
    duration: jitterDuration(prev.baseDuration ?? prev.duration, random),
    amp: Math.max(7, Math.round((prev.baseAmp ?? prev.amp ?? 11) * (0.85 + random() * 0.3))),
    opacity: jitterOpacity(prev.depth, random),
    delay: -(random() * 4),
    radius: proximityRadius(size),
  };
}
