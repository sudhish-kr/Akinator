import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { beatMs, CELEBRATE_MS, FOCUS_MS, MISS_MS } from "./guessBeat.js";

describe("guess screen beats", () => {
  it("keeps focus / celebrate / miss short", () => {
    assert.ok(FOCUS_MS >= 200 && FOCUS_MS <= 500);
    assert.ok(CELEBRATE_MS >= 200 && CELEBRATE_MS <= 500);
    assert.ok(MISS_MS >= 200 && MISS_MS <= 500);
  });

  it("skips delays when reduced motion is on", () => {
    assert.equal(beatMs("focus", true), 0);
    assert.equal(beatMs("celebrate", true), 0);
    assert.equal(beatMs("miss", true), 0);
  });

  it("uses the named beat when motion is allowed", () => {
    assert.equal(beatMs("focus", false), FOCUS_MS);
    assert.equal(beatMs("celebrate", false), CELEBRATE_MS);
    assert.equal(beatMs("miss", false), MISS_MS);
  });
});
