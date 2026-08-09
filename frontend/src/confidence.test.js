/**
 * Frontend confidence display / update helpers.
 * Run: node --test frontend/src/confidence.test.js
 */
import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { formatConfidencePercent, nextConfidence } from "./confidence.js";

describe("formatConfidencePercent", () => {
  it("shows 0 for empty confidence", () => {
    assert.equal(formatConfidencePercent(0), 0);
    assert.equal(formatConfidencePercent(null), 0);
  });

  it("shows one decimal under 1%", () => {
    assert.equal(formatConfidencePercent(0.002), 0.2);
  });

  it("rounds meaningful confidence", () => {
    assert.equal(formatConfidencePercent(0.42), 42);
    assert.equal(formatConfidencePercent(0.856), 86);
  });
});

describe("nextConfidence", () => {
  it("replaces with latest backend value", () => {
    assert.equal(nextConfidence(0.1, 0.45), 0.45);
  });

  it("does not keep stale when API sends 0", () => {
    assert.equal(nextConfidence(0.9, 0), 0);
  });

  it("keeps previous only when incoming is missing", () => {
    assert.equal(nextConfidence(0.33, undefined), 0.33);
    assert.equal(nextConfidence(0.33, null), 0.33);
  });
});

describe("wrong-guess selectable flow labels", () => {
  it("LearnPage type options cover required choices", async () => {
    const fs = await import("node:fs/promises");
    const path = new URL("./pages/LearnPage.jsx", import.meta.url);
    const src = await fs.readFile(path, "utf8");
    assert.match(src, /typeReal/);
    assert.match(src, /typeFictional/);
    assert.match(src, /typeAnimal/);
    assert.match(src, /typeOther/);
    assert.match(src, /step === "type"/);
    assert.match(src, /step === "category"/);
    assert.match(src, /step === "suggestions"/);
    assert.match(src, /step === "manual"/);
  });
});
