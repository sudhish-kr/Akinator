/**
 * Home-world ball proximity helpers.
 * Run: npm test
 */
import { describe, it } from "node:test";
import assert from "node:assert/strict";
import {
  BALL_PALETTE,
  isInsideProximity,
  lookOffset,
  pickBallColor,
  pickBallMood,
  proximityRadius,
  shouldActivate,
  staggerDelay,
} from "./components/homeBallInteract.js";

describe("home ball proximity", () => {
  it("clamps radius by ball size", () => {
    assert.equal(proximityRadius(22), 80);
    assert.equal(proximityRadius(96), 130);
    const mid = proximityRadius(50);
    assert.ok(mid > 80 && mid < 130);
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
