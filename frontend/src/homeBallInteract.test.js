/**
 * Home-world ball proximity helpers.
 * Run: npm test
 */
import { describe, it } from "node:test";
import assert from "node:assert/strict";
import {
  BALL_PALETTE,
  isClearOfPoint,
  isInsideProximity,
  lookOffset,
  nextBallSpec,
  pickBallColor,
  pickBallMood,
  pickSpawnPercent,
  proximityRadius,
  rectsOverlap,
  shouldActivate,
  staggerDelay,
} from "./components/homeBallInteract.js";

describe("home ball proximity", () => {
  it("clamps radius by ball size into a nearby-but-not-touch range", () => {
    assert.equal(proximityRadius(22), 64);
    assert.equal(proximityRadius(96), 100);
    const mid = proximityRadius(50);
    assert.ok(mid >= 60 && mid <= 100);
    assert.ok(mid > proximityRadius(22));
  });

  it("detects enter / leave without requiring a hit", () => {
    assert.equal(isInsideProximity(90, 0, 100), true);
    assert.equal(isInsideProximity(101, 0, 100), false);
  });

  it("looks toward the cursor, not through it", () => {
    const left = lookOffset(-80, 0, 100);
    const right = lookOffset(80, 0, 100);
    const up = lookOffset(0, -80, 100);
    assert.ok(left.x < 0);
    assert.ok(right.x > 0);
    assert.ok(up.y < 0);
    assert.ok(Math.abs(left.x) <= 2.4);
    assert.ok(Math.abs(up.y) <= 1.8);
  });

  it("picks a palette color, not arbitrary RGB", () => {
    const ids = new Set(BALL_PALETTE.map((c) => c.id));
    for (let i = 0; i < 20; i += 1) {
      const c = pickBallColor(null, () => i / 20);
      assert.ok(ids.has(c.id));
      assert.match(c.tint, /^#[0-9a-f]{6}$/i);
    }
    const next = pickBallColor("teal", () => 0);
    assert.notEqual(next.id, "teal");
  });

  it("activates on enter, not while remaining nearby", () => {
    assert.equal(shouldActivate({ inside: true, wasInside: false, now: 10, cooldownUntil: 0 }), true);
    assert.equal(shouldActivate({ inside: true, wasInside: true, now: 10, cooldownUntil: 0 }), false);
    assert.equal(shouldActivate({ inside: true, wasInside: false, now: 10, cooldownUntil: 50 }), false);
    assert.equal(shouldActivate({ inside: false, wasInside: false, now: 10, cooldownUntil: 0 }), false);
  });

  it("staggers simultaneous reactions", () => {
    assert.equal(staggerDelay(0), 0);
    assert.equal(staggerDelay(1), 55);
    assert.ok(staggerDelay(2) > staggerDelay(1));
  });

  it("varies facial mood so balls do not all react the same", () => {
    const moods = new Set();
    for (let i = 0; i < 12; i += 1) {
      moods.add(pickBallMood(null, () => i / 12));
    }
    assert.ok(moods.size >= 2);
    assert.notEqual(pickBallMood("happy", () => 0), "happy");
  });
});

describe("home ball respawn", () => {
  it("keeps spawn points clear of the cursor", () => {
    assert.equal(isClearOfPoint(10, 10, { x: 500, y: 400 }, 120), true);
    assert.equal(isClearOfPoint(500, 400, { x: 500, y: 400 }, 120), false);
    assert.equal(isClearOfPoint(560, 400, { x: 500, y: 400 }, 80), false);
  });

  it("detects overlap with UI keep-out rects", () => {
    const ui = { left: 300, top: 120, right: 700, bottom: 420 };
    assert.equal(rectsOverlap({ left: 10, top: 10, right: 50, bottom: 50 }, ui, 18), false);
    assert.equal(rectsOverlap({ left: 500, top: 200, right: 540, bottom: 240 }, ui, 18), true);
  });

  it("spawns away from the cursor instead of under it", () => {
    const spawn = pickSpawnPercent({
      rootRect: { left: 0, top: 0, width: 1000, height: 800 },
      mouse: { clientX: 500, clientY: 400 },
      size: 48,
      random: () => 0,
      attempts: 8,
    });
    const px = (spawn.x / 100) * 1000;
    const py = (spawn.y / 100) * 800;
    assert.ok(Math.hypot(px - 500, py - 400) >= proximityRadius(48) + 48);
  });

  it("falls back away from a blocked UI region", () => {
    const spawn = pickSpawnPercent({
      rootRect: { left: 0, top: 0, width: 1000, height: 800 },
      mouse: null,
      size: 40,
      avoidRects: [{ left: 0, top: 0, right: 400, bottom: 800 }],
      random: () => 0,
      attempts: 1,
    });
    const px = (spawn.x / 100) * 1000;
    assert.ok(px > 400);
  });

  it("randomizes a replacement ball without resetting the rest", () => {
    const prev = {
      size: 50,
      baseSize: 50,
      duration: 6,
      baseDuration: 6,
      amp: 12,
      baseAmp: 12,
      depth: 1,
    };
    const a = nextBallSpec(prev, { x: 80, y: 20 }, () => 0.1);
    const b = nextBallSpec(prev, { x: 12, y: 78 }, () => 0.9);
    assert.equal(a.x, 80);
    assert.equal(b.x, 12);
    assert.notEqual(a.size, b.size);
    assert.notEqual(a.duration, b.duration);
    assert.notEqual(a.opacity, b.opacity);
    assert.ok(a.opacity >= 0.28 && a.opacity <= 0.82);
    assert.ok(a.radius >= 60 && a.radius <= 100);
  });
});
